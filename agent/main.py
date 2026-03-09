"""CLI entry point for the IFS middleware log analysis RCA agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if __package__ in {None, ""}:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.collector.local_logs import read_log_events
from agent.correlate.root_cause_ranker import rank_root_causes
from agent.correlate.timeline import build_timeline
from agent.detect.rule_engine import apply_rules
from agent.report.render import render_markdown


def _load_rules(rules_file: Path) -> List[Dict[str, Any]]:
    payload = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError(f"Invalid rules format in {rules_file}")
    return rules


def _build_context(events: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = rank_root_causes(signals)
    top_signal = ranked[0] if ranked else None

    if top_signal:
        root_cause = top_signal.get("rca_hint", "Unknown")
        actions = top_signal.get("recommended_actions", [])
        summary = (
            f"Detected {len(signals)} signal(s) across {len(events)} log event(s). "
            f"Top candidate: {top_signal.get('rule_id')} ({top_signal.get('severity')})."
        )
    else:
        root_cause = "No known issue detected from current rule catalog"
        actions = ["Review raw logs and extend rules.yaml for your incident signatures."]
        summary = f"No rules matched. Parsed {len(events)} log event(s)."

    timeline_records = build_timeline(events)
    timeline = [
        {
            "timestamp": item.get("timestamp", "N/A"),
            "source": Path(item.get("source_file", "unknown")).name,
            "message": item.get("message", ""),
        }
        for item in timeline_records[:100]
    ]

    return {
        "summary": summary,
        "timeline": timeline,
        "root_cause": root_cause,
        "actions": actions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RCA analysis over local exported logs.")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=PROJECT_ROOT / "input_logs",
        help="Directory containing exported middleware logs (.log/.txt/.jsonl).",
    )
    parser.add_argument(
        "--rules-file",
        type=Path,
        default=PROJECT_ROOT / "agent/detect/rules.yaml",
        help="YAML rule catalog file.",
    )
    parser.add_argument(
        "--template-file",
        type=Path,
        default=PROJECT_ROOT / "agent/report/rca_template.md.j2",
        help="Jinja2 markdown template path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output",
        help="Directory where generated report is written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.log_dir.exists():
        raise SystemExit(f"Log directory not found: {args.log_dir}")
    if not args.rules_file.exists():
        raise SystemExit(f"Rules file not found: {args.rules_file}")
    if not args.template_file.exists():
        raise SystemExit(f"Template file not found: {args.template_file}")

    events = read_log_events(args.log_dir)
    rules = _load_rules(args.rules_file)
    signals = apply_rules(events, rules)

    context = _build_context(events, signals)
    report = render_markdown(context, args.template_file)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "rca_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"Parsed events : {len(events)}")
    print(f"Matched signals: {len(signals)}")
    print(f"Report written : {report_path.resolve()}")


if __name__ == "__main__":
    main()
