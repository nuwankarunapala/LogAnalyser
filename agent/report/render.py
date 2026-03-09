"""RCA report rendering helpers."""

from typing import Dict, Any, List


def _format_list(items: List[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def render_markdown(context: Dict[str, Any]) -> str:
    """Render a plain markdown RCA report from computed context."""
    summary = context.get("summary", "No summary")
    findings = context.get("findings", [])
    actions = context.get("actions", [])
    missing_info = context.get("missing_info", [])

    lines = [
        "# RCA Report",
        "",
        "## Summary",
        summary,
        "",
        "## Findings",
    ]

    if not findings:
        lines.append("- No known incident patterns were matched from the provided logs.")
    else:
        for finding in findings:
            lines.append(
                "- "
                f"[{finding['severity'].upper()}] {finding['rule_id']} "
                f"({finding['container_role']}) at {finding['source_file']}:{finding['line_no']}"
            )
            lines.append(f"  - Evidence: {finding['message']}")
            if finding.get("rca_hint"):
                lines.append(f"  - RCA hint: {finding['rca_hint']}")

    lines.extend(
        [
            "",
            "## Recommended Actions",
            _format_list(actions),
            "",
            "## Missing Information Required From User",
            _format_list(missing_info),
            "",
        ]
    )

    return "\n".join(lines)
