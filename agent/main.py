"""CLI entry point for the IFS middleware log analysis RCA agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.collector.local_logs import read_log_events
from agent.correlate.chatgpt_rca import infer_root_cause_with_chatgpt
from agent.correlate.root_cause_ranker import rank_root_causes
from agent.correlate.timeline import build_timeline
from agent.detect.rule_engine import apply_rules
from agent.report.render import render_markdown


MAX_REPORT_LOG_MESSAGE_LENGTH = 280


def _load_rules(rules_file: Path) -> List[Dict[str, Any]]:
    payload = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError(f"Invalid rules format in {rules_file}")
    return rules


def _build_context(
    events: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    ai_hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ranked = rank_root_causes(signals)
    top_signal = ranked[0] if ranked else None

    unresolved_rca = False

    if top_signal:
        root_cause = top_signal.get("rca_hint", "Unknown")
        actions = top_signal.get("recommended_actions", [])
        summary = (
            f"Detected {len(signals)} signal(s) across {len(events)} log event(s). "
            f"Top candidate: {top_signal.get('rule_id')} ({top_signal.get('severity')})."
        )
    else:
        unresolved_rca = True
        root_cause = "No known issue detected from current rule catalog"
        actions = [
            "Review raw logs and extend rules.yaml for your incident signatures.",
            "Collect additional Kubernetes context and rerun analysis.",
        ]
        summary = f"No rules matched. Parsed {len(events)} log event(s)."

    if ai_hint:
        if ai_hint.get("root_cause"):
            root_cause = ai_hint["root_cause"]
            unresolved_rca = False
        if ai_hint.get("executive_summary"):
            summary = ai_hint["executive_summary"]
        ai_actions = ai_hint.get("corrective_actions_planned", [])
        if ai_actions:
            actions = ai_actions

    if unresolved_rca:
        summary = (
            f"{summary} Root cause is still inconclusive with the current evidence. "
            "Please provide additional incident context and Kubernetes diagnostics."
        )
        actions.extend(
            [
                "Share recent deployment/configuration changes and exact user-facing symptoms.",
                "Run `kubectl get pods -A -o wide` and `kubectl describe pod <pod> -n <namespace>` for impacted workloads.",
                "Run `kubectl get events -A --sort-by=.metadata.creationTimestamp | tail -n 200` to capture recent cluster events.",
                "Run `kubectl logs <pod> -n <namespace> --previous --tail=200` for restarting containers.",
            ]
        )

    def _trim_message(record: Dict[str, Any]) -> Dict[str, Any]:
        msg = str(record.get("message", ""))
        if len(msg) > MAX_REPORT_LOG_MESSAGE_LENGTH:
            msg = f"{msg[:MAX_REPORT_LOG_MESSAGE_LENGTH]}... [truncated]"
        updated = dict(record)
        updated["message"] = msg
        return updated

    timeline_records = build_timeline(events)
    timeline = []
    for item in timeline_records[:100]:
        timeline.append(
            _trim_message(
                {
                    "timestamp": item.get("timestamp", "N/A"),
                    "source": Path(item.get("source_file", "unknown")).name,
                    "message": item.get("message", ""),
                }
            )
        )

    impacted_sources = sorted(
        {
            Path(item.get("source_file", "unknown")).name
            for item in timeline_records
            if item.get("source_file")
        }
    )

    return {
        "executive_summary": summary,
        "scope_impact": {
            "users": "TBD - confirm impacted customer/user segments",
            "transactions": f"{len(events)} log events reviewed, {len(signals)} signals matched",
            "duration": (
                f"{timeline_records[0].get('timestamp', 'N/A')} to "
                f"{timeline_records[-1].get('timestamp', 'N/A')}"
                if timeline_records
                else "N/A"
            ),
            "sla": "TBD - map incident window against service SLA/SLO targets",
        },
        "timeline": timeline,
        "technical_analysis": {
            "evidence_set": [
                f"Parsed {len(events)} log event(s) from {len(impacted_sources)} source file(s)",
                f"Detected {len(signals)} rule-based signal(s)",
            ],
            "healthy_vs_incident": [
                "Healthy baseline not provided in current dataset",
                "Incident behavior inferred from matched rule signatures and event clustering",
            ],
            "correlation": [
                (
                    f"Highest-ranked signal: {top_signal.get('rule_id')} "
                    f"(severity={top_signal.get('severity')}, matches={top_signal.get('match_count', 0)})"
                )
                if top_signal
                else "No direct rule correlation identified in this run"
            ],
        },
        "root_cause": root_cause,
        "corrective_actions_done": [
            "Automated triage completed against current rule catalog",
            "Timeline assembled from available log evidence",
        ],
        "corrective_actions_planned": actions,
        "preventive_actions": [
            {
                "action": "Expand rule catalog with incident-specific signatures",
                "owner": "SRE/Platform Team",
                "eta": "TBD",
                "risks": "Low - may increase false positives until tuned",
                "cab_required": "No",
            },
            {
                "action": "Add proactive alerts for top recurring failure modes",
                "owner": "Observability Team",
                "eta": "TBD",
                "risks": "Medium - alert noise if thresholds are not calibrated",
                "cab_required": "Yes (if production alert policy changes)",
            },
        ],
        "validation_plan": {
            "kpis": [
                "Error-rate trend for affected middleware components",
                "Signal recurrence count for the identified root-cause rule",
                "MTTD/MTTR for similar incidents",
            ],
            "success_criteria": [
                "No recurrence of the same high-severity signal for 7 consecutive days",
                "Service error-rate returns to normal operational baseline",
            ],
        },
        "appendix": {
            "log_excerpts": timeline[:10],
            "queries": [
                "Search for severity keywords and stack traces around incident window",
                "Filter logs by impacted namespace/pod and correlate with deploy times",
            ],
            "diagrams": ["TBD - attach architecture/sequence diagram if required"],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RCA analysis over local exported logs.")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("input_logs"),
        help="Directory containing exported middleware logs (.log/.txt/.jsonl).",
    )
    parser.add_argument(
        "--rules-file",
        type=Path,
        default=Path("agent/detect/rules.yaml"),
        help="YAML rule catalog file.",
    )
    parser.add_argument(
        "--template-file",
        type=Path,
        default=Path("agent/report/rca_template.md.j2"),
        help="Jinja2 markdown template path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where generated report is written.",
    )
    parser.add_argument(
        "--use-chatgpt",
        action="store_true",
        help="Enable optional ChatGPT-assisted RCA enrichment (requires OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--chatgpt-model",
        default="gpt-4.1-mini",
        help="Model used for ChatGPT-assisted RCA when --use-chatgpt is enabled.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.log_dir.exists():
        raise SystemExit(f"Log directory not found: {args.log_dir}")

    events = read_log_events(args.log_dir)
    rules = _load_rules(args.rules_file)
    signals = apply_rules(events, rules)

    ai_hint = None
    if args.use_chatgpt:
        ai_hint = infer_root_cause_with_chatgpt(events, signals, model=args.chatgpt_model)

    context = _build_context(events, signals, ai_hint=ai_hint)
    report = render_markdown(context, args.template_file)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "rca_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"Parsed events : {len(events)}")
    print(f"Matched signals: {len(signals)}")
    if args.use_chatgpt:
        print(f"ChatGPT hint  : {'used' if ai_hint else 'not available'}")
    print(f"Report written : {report_path.resolve()}")


if __name__ == "__main__":
    main()
