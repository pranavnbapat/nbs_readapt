from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services import RESPONSE_STYLES, run_assistant


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
