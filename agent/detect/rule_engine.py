"""Rule engine for incident signal detection."""

from typing import Dict, List, Any


def _message_matches(message: str, contains_any: List[str]) -> bool:
    message_lower = message.lower()
    return any(token.lower() in message_lower for token in contains_any)


def apply_rules(events: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply rule definitions to normalized events and return matched findings."""
    findings: List[Dict[str, Any]] = []

    for event in events:
        message = event.get("message", "")
        role = event.get("container_role", "any")

        for rule in rules:
            target_role = rule.get("target_container_role", "any")
            if target_role != "any" and target_role != role:
                continue

            contains_any = rule.get("match", {}).get("contains_any", [])
            if not contains_any:
                continue

            if _message_matches(message, contains_any):
                findings.append(
                    {
                        "rule_id": rule.get("id", "UNKNOWN"),
                        "category": rule.get("category", "unknown"),
                        "severity": rule.get("severity", "medium"),
                        "container_role": role,
                        "source_file": event.get("source_file", ""),
                        "line_no": event.get("line_no", 0),
                        "message": message,
                        "rca_hint": rule.get("rca_hint", ""),
                        "recommended_actions": rule.get("recommended_actions", []),
                    }
                )

    return findings
