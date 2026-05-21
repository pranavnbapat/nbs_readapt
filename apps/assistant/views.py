from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services import RESPONSE_STYLES, prepare_assistant_stream, run_assistant, run_assistant_stream


@require_GET
def assistant_status_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "status": "ok",
            "provider": "vllm",
            "configured": bool(settings.VLLM.get("base_url") and settings.VLLM.get("model") and settings.VLLM.get("api_key")),
            "model": settings.VLLM.get("model") or "",
            "response_styles": list(RESPONSE_STYLES.keys()),
            "default_response_style": settings.ASSISTANT["response_style_default"],
        }
    )


@csrf_exempt
@require_POST
def assistant_chat_view(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "error": "Invalid JSON body."}, status=400)

    query = str(payload.get("query") or "").strip()
    history = payload.get("history") or []
    response_style = str(payload.get("response_style") or "").strip().lower()

    if not query:
        return JsonResponse({"status": "error", "error": "Query is required."}, status=400)

    try:
        result = run_assistant(query=query, history=history, response_style=response_style)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": str(exc)}, status=400)
    except RuntimeError as exc:
        return JsonResponse({"status": "error", "error": str(exc)}, status=502)

    return JsonResponse(
        {
            "status": result.status,
            "reason": result.reason,
            "response_style": result.response_style,
            "grounded": result.grounded,
            "reply": result.reply,
            "sources": [
                {
                    "record_id": source.record_id,
                    "title": source.title,
                    "source_dataset": source.source_dataset,
                    "source_year": source.source_year,
                    "country_display": source.country_display,
                    "source_url": source.source_url,
                    "score": source.score,
                    "summary": source.summary,
                }
                for source in result.sources
            ],
        }
    )


@csrf_exempt
@require_POST
def assistant_chat_stream_view(request: HttpRequest) -> StreamingHttpResponse | JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "error": "Invalid JSON body."}, status=400)

    query = str(payload.get("query") or "").strip()
    history = payload.get("history") or []
    response_style = str(payload.get("response_style") or "").strip().lower()

    if not query:
        return JsonResponse({"status": "error", "error": "Query is required."}, status=400)

    try:
        prepared = prepare_assistant_stream(query=query, history=history, response_style=response_style)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": str(exc)}, status=400)
    except RuntimeError as exc:
        return JsonResponse({"status": "error", "error": str(exc)}, status=502)

    meta = {
        "type": "meta",
        "status": "ok",
        "reason": prepared.out_of_scope_result.reason if prepared.out_of_scope_result else ("grounded_answer" if prepared.included_sources else "general_answer"),
        "response_style": prepared.style,
        "grounded": bool(prepared.included_sources),
        "sources": [
            {
                "record_id": source.record_id,
                "title": source.title,
                "source_dataset": source.source_dataset,
                "source_year": source.source_year,
                "country_display": source.country_display,
                "source_url": source.source_url,
                "score": source.score,
                "summary": source.summary,
            }
            for source in prepared.included_sources
        ],
    }

    def event_stream():
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
        try:
            for chunk in run_assistant_stream(prepared):
                if chunk:
                    yield f"data: {json.dumps({'type': 'delta', 'text': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        except RuntimeError as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
