from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterator
from urllib import error, parse, request

from django.conf import settings

from apps.repository.models import Country, Hazard, NbsType, RepositoryRecord
from apps.search.opensearch import get_opensearch_client


@dataclass
class AssistantSource:
    record_id: int
    title: str
    source_dataset: str
    source_year: int | None
    country_display: str
    source_url: str
    score: float
    summary: str


@dataclass
class AssistantResult:
    reply: str
    sources: list[AssistantSource]
    status: str
    reason: str
    response_style: str
    grounded: bool


@dataclass
class AssistantPrepared:
    query: str
    style: str
    history_messages: list[dict[str, str]]
    messages_for_model: list[dict[str, str]]
    included_sources: list[AssistantSource]
    out_of_scope_result: AssistantResult | None = None


RESPONSE_STYLES: dict[str, dict[str, Any]] = {
    "brief": {
        "max_tokens": 220,
        "instruction": "Keep the answer compact. Prefer 3-5 short bullets or one short paragraph plus bullets.",
    },
    "standard": {
        "max_tokens": 500,
        "instruction": "Give a concise but useful answer. Prefer short paragraphs and flat bullets.",
    },
    "detailed": {
        "max_tokens": 900,
        "instruction": "Give a more detailed answer, but stay practical and well-structured.",
    },
}


def _truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _extract_history(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    max_messages = settings.ASSISTANT["max_history_messages"]
    for message in messages[-max_messages:]:
        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content[: settings.ASSISTANT["max_query_chars"]]})
    return cleaned


def _query_terms(text: str) -> set[str]:
    return {term.strip(".,:;!?()[]{}").lower() for term in text.split() if len(term.strip()) >= 3}


def _normalize_vocab_terms(values: list[str]) -> set[str]:
    terms: set[str] = set()
    for value in values:
        cleaned = " ".join((value or "").lower().split())
        if not cleaned:
            continue
        terms.add(cleaned)
        for part in cleaned.replace("/", " ").replace("-", " ").split():
            if len(part) >= 3:
                terms.add(part)
    return terms


@lru_cache(maxsize=1)
def _domain_vocabulary() -> set[str]:
    values: list[str] = []
    values.extend(Country.objects.values_list("name", flat=True))
    values.extend(Hazard.objects.values_list("name", flat=True))
    values.extend(NbsType.objects.values_list("name", flat=True))
    values.extend(
        value
        for value in RepositoryRecord.objects.exclude(source_dataset="").values_list("source_dataset", flat=True).distinct()
    )
    values.extend(
        value
        for value in RepositoryRecord.objects.exclude(policy_level="").values_list("policy_level", flat=True).distinct()[:50]
    )
    values.extend(
        value
        for value in RepositoryRecord.objects.exclude(implementation_stage="").values_list("implementation_stage", flat=True).distinct()[:50]
    )
    values.extend(
        value
        for value in RepositoryRecord.objects.exclude(geographic_scope="").values_list("geographic_scope", flat=True).distinct()[:50]
    )
    values.extend(
        value
        for value in RepositoryRecord.objects.exclude(territorial_context="").values_list("territorial_context", flat=True).distinct()[:50]
    )
    return _normalize_vocab_terms([str(value) for value in values if value])


def _search_records(query: str, size: int | None = None) -> list[AssistantSource]:
    client = get_opensearch_client()
    body = {
        "size": size or settings.ASSISTANT["context_records"],
        "_source": [
            "record_id",
            "title",
            "source_dataset",
            "source_year",
            "country_display",
            "source_url",
            "summary",
            "abstract",
            "description",
            "lessons",
            "barriers",
            "enablers",
            "all_hazards",
            "all_nbs_types",
            "policy_level",
            "implementation_stage",
            "funding_source",
        ],
        "query": {
            "multi_match": {
                "query": query,
                "fields": [
                    "title^5",
                    "search_text^3",
                    "keywords^2",
                    "abstract^2",
                    "summary^2",
                    "description",
                    "all_hazards^2",
                    "all_nbs_types^2",
                    "funding_source^2",
                ],
                "type": "best_fields",
                "operator": "or",
            }
        },
        "sort": ["_score", {"source_year": {"order": "desc", "missing": "_last"}}],
    }
    response = client.search(index=settings.OPENSEARCH["index_bm25"], body=body)
    results: list[AssistantSource] = []
    for hit in response.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        combined_summary = source.get("summary") or source.get("abstract") or source.get("description") or ""
        results.append(
            AssistantSource(
                record_id=int(source.get("record_id") or 0),
                title=str(source.get("title") or "Untitled record"),
                source_dataset=str(source.get("source_dataset") or ""),
                source_year=source.get("source_year"),
                country_display=str(source.get("country_display") or ""),
                source_url=str(source.get("source_url") or ""),
                score=float(hit.get("_score") or 0.0),
                summary=_truncate(combined_summary, settings.ASSISTANT["context_field_chars"]),
            )
        )
    return results


def _is_relevant(query: str, history: list[dict[str, str]], sources: list[AssistantSource]) -> bool:
    if not query.strip():
        return False
    query_terms = _query_terms(query)
    if query_terms & _domain_vocabulary():
        return True
    if history:
        if len(query_terms) <= 8:
            return True
    if sources and sources[0].score >= settings.ASSISTANT["relevance_min_score"]:
        return True
    return False


def _source_label(source: AssistantSource) -> str:
    parts = [source.title]
    meta = [source.source_dataset or "", source.country_display or "", str(source.source_year or "")]
    meta = [value for value in meta if value]
    if meta:
        parts.append(" | ".join(meta))
    return " | ".join(parts)


def _build_context_block(sources: list[AssistantSource]) -> str:
    record_limit = settings.ASSISTANT["context_record_chars"]
    blocks = []
    for index, source in enumerate(sources, start=1):
        fields = [
            f"Title: {source.title}",
            f"Dataset: {source.source_dataset}",
            f"Year: {source.source_year or 'unknown'}",
            f"Country: {source.country_display or 'unspecified'}",
            f"Score: {source.score:.2f}",
        ]
        if source.source_url:
            fields.append(f"URL: {source.source_url}")
        if source.summary:
            fields.append(f"Evidence excerpt: {source.summary}")
        text = _truncate("\n".join(fields), record_limit)
        blocks.append(f"Record {index}\n{text}")
    return "\n\n".join(blocks)


def _estimate_tokens(*parts: str) -> int:
    chars_per_token = max(settings.ASSISTANT["approx_chars_per_token"], 1.0)
    text = "".join(part for part in parts if part)
    if not text:
        return 0
    return math.ceil(len(text) / chars_per_token)


def _provider_name() -> str:
    provider = (settings.ASSISTANT.get("provider") or "vllm").strip().lower()
    if provider not in {"vllm", "anthropic"}:
        raise RuntimeError(f"Unsupported assistant provider: {provider}")
    return provider


def _provider_config() -> dict[str, Any]:
    return settings.VLLM if _provider_name() == "vllm" else settings.ANTHROPIC


def _input_token_budget(response_style: str) -> int:
    model_len = max(int(_provider_config().get("max_model_len") or 0), 4096)
    output_tokens = RESPONSE_STYLES[response_style]["max_tokens"]
    configured = settings.ASSISTANT["max_input_tokens"]
    derived_margin = max(output_tokens * 2, 1024)
    safety_margin = settings.ASSISTANT["token_safety_margin"] or derived_margin
    budget = model_len - safety_margin
    if configured > 0:
        budget = min(budget, configured)
    return max(budget, 1024)


def _fit_messages_to_budget(
    system_prompt: str,
    history_messages: list[dict[str, str]],
    query: str,
    sources: list[AssistantSource],
    response_style: str,
) -> tuple[list[dict[str, str]], list[AssistantSource]]:
    budget = _input_token_budget(response_style)
    trimmed_history = list(history_messages)

    # Keep the raw user query first; history is the cheapest thing to drop.
    query_text = _truncate(query, settings.ASSISTANT["max_query_chars"])

    while trimmed_history:
        history_text = "\n".join(message["content"] for message in trimmed_history)
        if _estimate_tokens(system_prompt, history_text, query_text) <= budget:
            break
        trimmed_history.pop(0)

    included_sources: list[AssistantSource] = []
    context_blocks: list[str] = []
    for source in sources:
        candidate_blocks = [*context_blocks]
        fields = [
            f"Title: {source.title}",
            f"Dataset: {source.source_dataset}",
            f"Year: {source.source_year or 'unknown'}",
            f"Country: {source.country_display or 'unspecified'}",
            f"Score: {source.score:.2f}",
        ]
        if source.source_url:
            fields.append(f"URL: {source.source_url}")
        if source.summary:
            fields.append(f"Evidence excerpt: {source.summary}")
        candidate_blocks.append(f"Record {len(candidate_blocks) + 1}\n{_truncate(chr(10).join(fields), settings.ASSISTANT['context_record_chars'])}")
        context_text = "\n\nRepository context:\n" + "\n\n".join(candidate_blocks)
        history_text = "\n".join(message["content"] for message in trimmed_history)
        if _estimate_tokens(system_prompt, history_text, query_text, context_text) > budget:
            break
        context_blocks = candidate_blocks
        included_sources.append(source)

    user_content = query_text
    if context_blocks:
        user_content = f"{query_text}\n\nRepository context:\n" + "\n\n".join(context_blocks)

    # Final defensive trim if even query + minimal history is still too large.
    history_text = "\n".join(message["content"] for message in trimmed_history)
    remaining_for_user = max(budget - _estimate_tokens(system_prompt, history_text), 256)
    if _estimate_tokens(user_content) > remaining_for_user:
        max_chars = max(int(remaining_for_user * settings.ASSISTANT["approx_chars_per_token"]), 512)
        user_content = _truncate(user_content, max_chars)

    return [*trimmed_history, {"role": "user", "content": user_content}], included_sources


def _build_system_prompt(response_style: str) -> str:
    style_config = RESPONSE_STYLES[response_style]
    return "\n".join(
        [
            "You are the NbS Repository Assistant for ESPON ReAdapt.",
            "Your role is to answer questions about nature-based solutions, climate adaptation evidence, projects, policies, funding, and comparable repository records.",
            "Ground your answer in the provided repository context whenever relevant.",
            "If the evidence is thin or mixed, say so clearly.",
            "Do not invent records, projects, policies, URLs, or statistics.",
            "If the user asks something outside repository scope, refuse briefly and redirect them back to NbS, adaptation, funding, policy, or evidence questions.",
            "When using repository evidence, cite records inline as [Source: title].",
            "Prefer practical, decision-useful language over generic theory.",
            style_config["instruction"],
            "End with a short next step only if it genuinely helps.",
        ]
    )


def _out_of_scope_reply() -> str:
    return (
        "I can help with questions about Nature-based Solutions, climate adaptation evidence, policies, "
        "funding, projects, and comparable cases in this repository. Please ask something within that scope, "
        "for example urban flooding NbS options, EU funding, policy requirements, or relevant case studies."
    )


def _vllm_chat_completion_url() -> str:
    explicit = settings.VLLM.get("chat_completions_url") or ""
    if explicit:
        return explicit
    base_url = settings.VLLM.get("base_url") or ""
    if not base_url:
        raise RuntimeError("VLLM base URL is not configured.")
    return parse.urljoin(f"{base_url}/", "v1/chat/completions")


def _anthropic_messages_url() -> str:
    base_url = settings.ANTHROPIC.get("base_url") or ""
    if not base_url:
        raise RuntimeError("Anthropic base URL is not configured.")
    return parse.urljoin(f"{base_url}/", "v1/messages")


def _read_json_response(req: request.Request) -> dict[str, Any]:
    timeout = settings.ASSISTANT["timeout_seconds"]
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Model API connection failed: {exc.reason}") from exc
    return json.loads(raw)


def _call_vllm(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> str:
    model = settings.VLLM.get("model") or ""
    if not model:
        raise RuntimeError("VLLM model is not configured.")

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "temperature": 0.2,
        "max_tokens": RESPONSE_STYLES[response_style]["max_tokens"],
        "stream": False,
    }
    req = request.Request(
        _vllm_chat_completion_url(),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; NbS-ReAdapt-Assistant/1.0; +https://nbs-readapt.example.com)",
            "Authorization": f"Bearer {settings.VLLM.get('api_key') or ''}",
        },
    )
    payload = _read_json_response(req)
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("Model API returned no choices.")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "\n".join(part for part in text_parts if part).strip()
    raise RuntimeError("Model API returned an unexpected message format.")


def _call_vllm_stream(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> Iterator[str]:
    model = settings.VLLM.get("model") or ""
    if not model:
        raise RuntimeError("VLLM model is not configured.")

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "temperature": 0.2,
        "max_tokens": RESPONSE_STYLES[response_style]["max_tokens"],
        "stream": True,
    }
    req = request.Request(
        _vllm_chat_completion_url(),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (compatible; NbS-ReAdapt-Assistant/1.0; +https://nbs-readapt.example.com)",
            "Authorization": f"Bearer {settings.VLLM.get('api_key') or ''}",
        },
    )
    timeout = settings.ASSISTANT["timeout_seconds"]
    try:
        with request.urlopen(req, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_line = line[5:].strip()
                if not data_line or data_line == "[DONE]":
                    break
                try:
                    payload = json.loads(data_line)
                except json.JSONDecodeError:
                    continue
                choices = payload.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("text"):
                            yield str(item["text"])
                if choices[0].get("finish_reason"):
                    break
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Model API connection failed: {exc.reason}") from exc


def _call_anthropic(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> str:
    model = settings.ANTHROPIC.get("model") or ""
    api_key = settings.ANTHROPIC.get("api_key") or ""
    if not model:
        raise RuntimeError("Anthropic model is not configured.")
    if not api_key:
        raise RuntimeError("Anthropic API key is not configured.")

    payload = {
        "model": model,
        "system": system_prompt,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": RESPONSE_STYLES[response_style]["max_tokens"],
    }
    req = request.Request(
        _anthropic_messages_url(),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; NbS-ReAdapt-Assistant/1.0; +https://nbs-readapt.example.com)",
            "x-api-key": api_key,
            "anthropic-version": settings.ANTHROPIC.get("version") or "2023-06-01",
        },
    )
    payload = _read_json_response(req)
    content = payload.get("content") or []
    text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
    reply = "\n".join(part for part in text_parts if part).strip()
    if reply:
        return reply
    raise RuntimeError("Anthropic API returned no text content.")


def _call_anthropic_stream(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> Iterator[str]:
    model = settings.ANTHROPIC.get("model") or ""
    api_key = settings.ANTHROPIC.get("api_key") or ""
    if not model:
        raise RuntimeError("Anthropic model is not configured.")
    if not api_key:
        raise RuntimeError("Anthropic API key is not configured.")

    payload = {
        "model": model,
        "system": system_prompt,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": RESPONSE_STYLES[response_style]["max_tokens"],
        "stream": True,
    }
    req = request.Request(
        _anthropic_messages_url(),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (compatible; NbS-ReAdapt-Assistant/1.0; +https://nbs-readapt.example.com)",
            "x-api-key": api_key,
            "anthropic-version": settings.ANTHROPIC.get("version") or "2023-06-01",
        },
    )
    timeout = settings.ASSISTANT["timeout_seconds"]
    try:
        with request.urlopen(req, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_line = line[5:].strip()
                if not data_line:
                    continue
                try:
                    payload = json.loads(data_line)
                except json.JSONDecodeError:
                    continue
                event_type = payload.get("type") or ""
                if event_type == "content_block_delta":
                    delta = payload.get("delta") or {}
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        yield str(delta["text"])
                elif event_type == "message_stop":
                    break
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API HTTP {exc.code}: {body[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Model API connection failed: {exc.reason}") from exc


def _call_model(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> str:
    provider = _provider_name()
    if provider == "anthropic":
        return _call_anthropic(messages=messages, system_prompt=system_prompt, response_style=response_style)
    return _call_vllm(messages=messages, system_prompt=system_prompt, response_style=response_style)


def _call_model_stream(messages: list[dict[str, str]], system_prompt: str, response_style: str) -> Iterator[str]:
    provider = _provider_name()
    if provider == "anthropic":
        yield from _call_anthropic_stream(messages=messages, system_prompt=system_prompt, response_style=response_style)
        return
    yield from _call_vllm_stream(messages=messages, system_prompt=system_prompt, response_style=response_style)

def _prepare_assistant(query: str, history: list[dict[str, Any]] | None = None, response_style: str | None = None) -> AssistantPrepared:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query cannot be empty.")
    cleaned_query = _truncate(cleaned_query, settings.ASSISTANT["max_query_chars"])

    style = (response_style or settings.ASSISTANT["response_style_default"]).strip().lower()
    if style not in RESPONSE_STYLES:
        style = settings.ASSISTANT["response_style_default"]

    history_messages = _extract_history(history or [])
    sources = _search_records(cleaned_query)
    relevant = _is_relevant(cleaned_query, history_messages, sources)
    if not relevant:
        return AssistantPrepared(
            query=cleaned_query,
            style=style,
            history_messages=history_messages,
            messages_for_model=[],
            included_sources=[],
            out_of_scope_result=AssistantResult(
                reply=_out_of_scope_reply(),
                sources=[],
                status="ok",
                reason="out_of_scope",
                response_style=style,
                grounded=False,
            ),
        )

    messages_for_model, included_sources = _fit_messages_to_budget(
        system_prompt=_build_system_prompt(style),
        history_messages=history_messages,
        query=cleaned_query,
        sources=sources,
        response_style=style,
    )
    return AssistantPrepared(
        query=cleaned_query,
        style=style,
        history_messages=history_messages,
        messages_for_model=messages_for_model,
        included_sources=included_sources,
    )


def run_assistant(query: str, history: list[dict[str, Any]] | None = None, response_style: str | None = None) -> AssistantResult:
    prepared = _prepare_assistant(query=query, history=history, response_style=response_style)
    if prepared.out_of_scope_result is not None:
        return prepared.out_of_scope_result

    reply = _call_model(
        messages=prepared.messages_for_model,
        system_prompt=_build_system_prompt(prepared.style),
        response_style=prepared.style,
    )
    return AssistantResult(
        reply=reply,
        sources=prepared.included_sources,
        status="ok",
        reason="grounded_answer" if prepared.included_sources else "general_answer",
        response_style=prepared.style,
        grounded=bool(prepared.included_sources),
    )


def prepare_assistant_stream(query: str, history: list[dict[str, Any]] | None = None, response_style: str | None = None) -> AssistantPrepared:
    return _prepare_assistant(query=query, history=history, response_style=response_style)


def run_assistant_stream(prepared: AssistantPrepared) -> Iterator[str]:
    if prepared.out_of_scope_result is not None:
        yield prepared.out_of_scope_result.reply
        return
    yield from _call_model_stream(
        messages=prepared.messages_for_model,
        system_prompt=_build_system_prompt(prepared.style),
        response_style=prepared.style,
    )
