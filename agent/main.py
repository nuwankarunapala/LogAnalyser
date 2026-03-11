from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from agent.file_discovery import discover_dump_files, flatten_discovered
from agent.openai_assistant import refine_with_openai
from agent.parsers import filter_window, parse_discovered_file
from agent.pattern_library import load_pattern_library
from agent.rca_writer import write_outputs
from agent.root_cause_engine import score_root_causes
from agent.timeline_builder import build_timeline, summarize_top_errors

logger = logging.getLogger("log_analyser")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IFS Kubernetes dump RCA analyser")
    parser.add_argument("--dump-folder", type=Path, required=True)
    parser.add_argument("--outage-start", required=True, help="YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--use-openai", action="store_true")
    parser.add_argument("--openai-model", default="gpt-4.1-mini")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--pattern-file", type=Path, default=Path("agent/detect/ifs_k8s_patterns.yaml"))
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def _parse_outage_start(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise SystemExit(f"Invalid --outage-start format: {value}. Use YYYY-MM-DD HH:MM:SS") from exc


def _build_additional_questions(primary_confidence: int) -> List[str]:
    if primary_confidence >= 60:
        return []
    return [
        "Was there a deployment during the outage window?",
        "Was database slowness or listener outage reported?",
        "Were users seeing HTTP 502, login failures, or full outage?",
        "Were any pods manually restarted during incident response?",
        "Can you provide DB alert logs and kubectl get events output?",
    ]


def run_analysis(args: argparse.Namespace) -> Dict[str, Any]:
    outage_start = _parse_outage_start(args.outage_start)
    patterns = load_pattern_library(args.pattern_file)

    discovered = discover_dump_files(args.dump_folder)
    files = list(flatten_discovered(discovered))
    logger.info("Discovered %s files across %s categories", len(files), len(discovered))

    events = []
    for entry in files:
        logger.debug("Parsing %s [%s]", entry.path, entry.source_type)
        events.extend(parse_discovered_file(entry, patterns))

    logger.info("Parsed %s total log lines/events", len(events))
    focused_events = filter_window(events, outage_start, args.window_minutes)
    logger.info("Focused event set size: %s", len(focused_events))

    ranked_causes = score_root_causes(focused_events)
    primary = ranked_causes[0] if ranked_causes else {"category": "Unknown", "confidence": 0, "score": 0, "count": 0, "evidence": []}

    timeline_events = build_timeline(focused_events)
    top_errors = summarize_top_errors(focused_events)
    evidence_snippets = primary.get("evidence", [])

    affected_components = sorted({e.component for e in focused_events})
    observed_errors = [entry["signal"] for entry in top_errors[:5]]

    report: Dict[str, Any] = {
        "executive_summary": (
            f"Outage analysis around {outage_start} indicates primary failure category '{primary['category']}' "
            f"with confidence {primary.get('confidence', 0)}%."
        ),
        "scope_impact": {
            "affected_users_services": "Unknown from dump alone; validate with incident channel/business report.",
            "affected_components": affected_components,
            "observed_errors": observed_errors,
            "outage_duration": "Unknown (inferred window only)",
            "sla_impact": "Unknown",
        },
        "timeline": [
            {
                "timestamp": e.timestamp.isoformat() if e.timestamp else "N/A",
                "source_type": e.source_type,
                "component": e.component,
                "message": e.message,
            }
            for e in timeline_events[:150]
        ],
        "primary_root_cause": primary,
        "secondary_contributors": ranked_causes[1:4],
        "root_cause_statement": f"Most likely root cause: {primary['category']} based on correlated event frequency/severity across components.",
        "corrective_actions": [
            "Validate impacted component health and restart stability.",
            "Confirm infrastructure dependencies (DB/network/ingress) are healthy.",
            "Review changes/deployments overlapping outage window.",
        ],
        "preventive_actions": [
            "Add targeted alerts for repeated signatures (ORA, 502/503, probe failures, CrashLoopBackOff).",
            "Increase runbook coverage for IFS outage triage and required artifacts.",
        ],
        "validation_plan": {
            "kpis": ["5xx rate", "pod restarts", "DB timeout rate", "probe failure count"],
            "success_criteria": ["No repeat critical patterns for 24h", "error rates return to baseline"],
        },
        "evidence_snippets": evidence_snippets,
        "file_references": [str(f.path) for f in files[:50]],
        "queries_used": [pattern["name"] for pattern in patterns],
        "additional_information_required": _build_additional_questions(primary.get("confidence", 0)),
        "recommended_additional_artifacts": [
            "kubectl get events -A --sort-by=.metadata.creationTimestamp",
            "database alert logs",
            "affected pod logs for wider range",
            "ingress controller events",
            "deployment change details",
        ],
        "analysis_stats": {
            "total_files": len(files),
            "total_events": len(events),
            "window_events": len(focused_events),
            "categories_detected": len(ranked_causes),
        },
    }

    if args.use_openai:
        condensed = {
            "outage_time": args.outage_start,
            "suspected_components": affected_components,
            "timeline": report["timeline"][:30],
            "top_errors": top_errors,
            "evidence_snippets": evidence_snippets,
            "local_hypothesis": primary,
            "missing_information": report["additional_information_required"],
        }
        ai_hint = refine_with_openai(condensed, model=args.openai_model)
        if ai_hint:
            report["openai_assist"] = ai_hint
            if ai_hint.get("likely_root_cause"):
                report["root_cause_statement"] = f"Most likely root cause: {ai_hint['likely_root_cause']}"

    return report


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    if not args.dump_folder.exists():
        raise SystemExit(f"Dump folder not found: {args.dump_folder}")

    report = run_analysis(args)
    write_outputs(report, args.output_dir)
    logger.info("RCA outputs written to %s", args.output_dir.resolve())


if __name__ == "__main__":
    main()
