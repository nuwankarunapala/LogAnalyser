from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib import error, request

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def refine_with_openai(summary_payload: Dict[str, Any], model: str, timeout_s: int = 45) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = {
        "task": "Refine RCA hypothesis using condensed evidence only",
        "instructions": [
            "Do not request raw logs; use provided evidence.",
            "Return JSON with keys: likely_root_cause, contributing_factors, corrective_actions, preventive_actions, evidence_gaps.",
        ],
        "evidence": summary_payload,
    }

    payload = {
        "model": model,
        "input": json.dumps(prompt, ensure_ascii=False),
        "text": {"format": {"type": "json_object"}},
    }

    req = request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_s) as response:
            body = json.loads(response.read().decode("utf-8"))
            output_text = body.get("output_text", "")
            return json.loads(output_text) if output_text else None
    except (error.URLError, error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        return None
