from __future__ import annotations

import json
from functools import wraps

from django.conf import settings
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services import RESPONSE_STYLES, prepare_assistant_stream, run_assistant, run_assistant_stream

ASSISTANT_SESSION_KEY = "assistant_session_active"
ASSISTANT_SESSION_USER_KEY = "assistant_session_user"


def _assistant_auth_configured() -> bool:
    config = settings.ASSISTANT_AUTH
    return bool(config.get("username") and config.get("password"))


def _touch_assistant_session(request: HttpRequest) -> None:
    request.session.set_expiry(settings.ASSISTANT_AUTH["session_timeout_seconds"])
    request.session.modified = True


def _assistant_session_active(request: HttpRequest, *, touch: bool = False) -> bool:
    active = bool(request.session.get(ASSISTANT_SESSION_KEY))
    if active and touch:
        _touch_assistant_session(request)
    return active


def _assistant_auth_payload(request: HttpRequest) -> dict[str, object]:
    active = _assistant_session_active(request)
    return {
        "status": "ok",
        "authenticated": active,
        "configured": _assistant_auth_configured(),
        "username": request.session.get(ASSISTANT_SESSION_USER_KEY, "") if active else "",
        "timeout_seconds": settings.ASSISTANT_AUTH["session_timeout_seconds"],
    }


def assistant_session_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not _assistant_session_active(request, touch=True):
            return JsonResponse(
                {
                    "status": "error",
                    "error": "Assistant login required.",
                    "code": "assistant_auth_required",
                },
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped


@csrf_exempt
@require_POST
def assistant_login_view(request: HttpRequest) -> JsonResponse:
    if not _assistant_auth_configured():
        return JsonResponse(
            {
                "status": "error",
                "error": "Assistant login is not configured.",
                "code": "assistant_auth_not_configured",
            },
            status=503,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "error": "Invalid JSON body."}, status=400)

    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    if username != settings.ASSISTANT_AUTH["username"] or password != settings.ASSISTANT_AUTH["password"]:
        return JsonResponse(
            {
                "status": "error",
                "error": "Invalid assistant username or password.",
                "code": "assistant_auth_invalid",
            },
            status=403,
        )

    request.session.cycle_key()
    request.session[ASSISTANT_SESSION_KEY] = True
    request.session[ASSISTANT_SESSION_USER_KEY] = username
    _touch_assistant_session(request)
    return JsonResponse(_assistant_auth_payload(request))


@csrf_exempt
@require_POST
def assistant_logout_view(request: HttpRequest) -> JsonResponse:
    request.session.pop(ASSISTANT_SESSION_KEY, None)
    request.session.pop(ASSISTANT_SESSION_USER_KEY, None)
    request.session.modified = True
    return JsonResponse(_assistant_auth_payload(request))


@require_GET
def assistant_session_view(request: HttpRequest) -> JsonResponse:
    touch = request.GET.get("touch") == "1"
    if _assistant_session_active(request, touch=touch):
        return JsonResponse(_assistant_auth_payload(request))
    return JsonResponse(_assistant_auth_payload(request), status=401)


@require_GET
@assistant_session_required
def assistant_status_view(request: HttpRequest) -> JsonResponse:
    provider = settings.ASSISTANT.get("provider") or "vllm"
    provider_config = settings.VLLM if provider == "vllm" else settings.ANTHROPIC
    configured = bool(provider_config.get("model") and provider_config.get("api_key"))
    if provider == "vllm":
        configured = configured and bool(provider_config.get("base_url") or provider_config.get("chat_completions_url"))
    else:
        configured = configured and bool(provider_config.get("base_url"))

    return JsonResponse(
        {
            "status": "ok",
            "provider": provider,
            "configured": configured,
            "model": provider_config.get("model") or "",
            "response_styles": list(RESPONSE_STYLES.keys()),
            "default_response_style": settings.ASSISTANT["response_style_default"],
        }
    )


@csrf_exempt
@require_POST
@assistant_session_required
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
@assistant_session_required
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
