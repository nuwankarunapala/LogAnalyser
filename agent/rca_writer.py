from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _md_list(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def render_rca_markdown(report: Dict[str, Any]) -> str:
    timeline_lines = []
    for item in report["timeline"]:
        timeline_lines.append(f"- {item['timestamp']} | {item['source_type']} | {item['component']} | {item['message']}")

    appendix = []
    for ev in report["evidence_snippets"]:
        appendix.append(f"- [{ev['timestamp']}] {ev['source']}: {ev['message']}")

    return f"""# Incident RCA Report

## 1. Executive Summary
{report['executive_summary']}

## 2. Scope & Impact
- **Affected users/services:** {report['scope_impact']['affected_users_services']}
- **Affected components:** {', '.join(report['scope_impact']['affected_components']) or 'Unknown'}
- **Observed errors:** {', '.join(report['scope_impact']['observed_errors']) or 'Unknown'}
- **Outage duration:** {report['scope_impact']['outage_duration']}
- **SLA impact:** {report['scope_impact']['sla_impact']}

## 3. Timeline of Events
{chr(10).join(timeline_lines) if timeline_lines else '- No timestamped events available'}

## 4. Technical Analysis
- Evidence set built from pod logs/descriptions, ingress, linkerd, deployment/job descriptions and autoscaler artifacts when present.
- Primary category score: {report['primary_root_cause'].get('score', 0)}.
- Confidence: {report['primary_root_cause'].get('confidence', 0)}%.

## 5. Root Cause
{report['root_cause_statement']}

## 6. Corrective Actions
### Done/Planned
{_md_list(report['corrective_actions'])}

## 7. Preventive Actions
{_md_list(report['preventive_actions'])}

## 8. Validation Plan
- **KPIs to monitor:** {', '.join(report['validation_plan']['kpis'])}
- **Success criteria:** {', '.join(report['validation_plan']['success_criteria'])}

## 9. Appendix
### Log excerpts
{chr(10).join(appendix) if appendix else '- None'}

### File references
{_md_list(report['file_references'])}

### Notable queries/patterns used
{_md_list(report['queries_used'])}

## Additional information required
{_md_list(report['additional_information_required'])}
"""


def write_outputs(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "incident_rca.md").write_text(render_rca_markdown(report), encoding="utf-8")
    (output_dir / "incident_rca.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    timeline_txt = "\n".join(
        f"{item['timestamp']} | {item['source_type']} | {item['component']} | {item['message']}" for item in report["timeline"]
    )
    (output_dir / "timeline.txt").write_text(timeline_txt, encoding="utf-8")
