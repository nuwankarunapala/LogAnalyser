"""Rule engine for incident signal detection."""

from __future__ import annotations

from typing import Any, Dict, List

SEVERITY_SCORES = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def apply_rules(events: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply rule definitions to normalized events and return matched signal summaries."""
    signals: List[Dict[str, Any]] = []

    for rule in rules:
        contains_any = [t.lower() for t in rule.get("match", {}).get("contains_any", [])]
        target_role = rule.get("target_container_role")
        matched_events: List[Dict[str, Any]] = []

        for event in events:
            if target_role and event.get("container_role") != target_role:
                continue

            message = str(event.get("message", "")).lower()
            if contains_any and any(token in message for token in contains_any):
                matched_events.append(event)

        if matched_events:
            severity = str(rule.get("severity", "low")).lower()
            signals.append(
                {
                    "rule_id": rule.get("id", "unknown"),
                    "category": rule.get("category", "unknown"),
                    "severity": severity,
                    "severity_score": SEVERITY_SCORES.get(severity, 1),
                    "match_count": len(matched_events),
                    "rca_hint": rule.get("rca_hint", "Unknown"),
                    "recommended_actions": rule.get("recommended_actions", []),
                    "evidence": matched_events[:5],
                }
            )

    return signals
