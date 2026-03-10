"""Optional ChatGPT-based RCA inference helper."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib import error, request


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def _build_prompt(events: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> str:
    """Build a compact RCA prompt payload."""
    event_sample = events[:20]
    signal_sample = signals[:20]
    return (
        "You are an SRE assistant. Analyze the incident evidence and respond in JSON with keys: "
        "root_cause, executive_summary, corrective_actions_planned. "
        "Keep root_cause concise, summary in plain English, and actions as array of short bullets.\n\n"
        f"Signal count: {len(signals)}\n"
        f"Event count: {len(events)}\n"
        f"Signals sample: {json.dumps(signal_sample, ensure_ascii=False)}\n"
        f"Events sample: {json.dumps(event_sample, ensure_ascii=False)}"
    )


def infer_root_cause_with_chatgpt(
    events: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    model: str,
    timeout_s: int = 30,
) -> Optional[Dict[str, Any]]:
    """Return ChatGPT RCA hints or None when not configured/failed."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": model,
        "input": _build_prompt(events, signals),
        "text": {"format": {"type": "json_object"}},
    }

    req = request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
    except (TimeoutError, error.HTTPError, error.URLError, OSError):
        return None

    try:
        parsed = json.loads(body)
        output_text = parsed.get("output_text", "")
        if not output_text:
            return None
        answer = json.loads(output_text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    root_cause = str(answer.get("root_cause", "")).strip()
    executive_summary = str(answer.get("executive_summary", "")).strip()
    actions = answer.get("corrective_actions_planned", [])

    if not isinstance(actions, list):
        actions = [str(actions)]

    if not root_cause and not executive_summary and not actions:
        return None

    return {
        "root_cause": root_cause,
        "executive_summary": executive_summary,
        "corrective_actions_planned": [str(a) for a in actions if str(a).strip()],
    }
