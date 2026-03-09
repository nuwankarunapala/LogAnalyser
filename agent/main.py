"""Entry point for the IFS middleware log analysis RCA agent."""

import argparse
from collections import Counter
import importlib
import importlib.util
from pathlib import Path
import sys
from typing import Any, Dict, List

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from agent.collector.local_logs import read_log_events
from agent.detect.rule_engine import apply_rules
from agent.report.render import render_markdown


def load_rules(rules_path: Path) -> List[Dict[str, Any]]:
    """Load rules from YAML when dependency exists; otherwise use built-in defaults."""
    yaml_spec = importlib.util.find_spec("yaml")
    if yaml_spec is None:
        return [
            {
                "id": "OOM_MAIN_001",
                "category": "oom",
                "severity": "high",
                "target_container_role": "main",
                "match": {"contains_any": ["OOMKilled", "MemoryPressure", "Evicted"]},
                "rca_hint": "Main container memory limit too low or sudden workload spike",
                "recommended_actions": [
                    "Check memory requests/limits",
                    "Review recent traffic spikes",
                ],
            },
            {
                "id": "IAM_AUTH_001",
                "category": "authentication",
                "severity": "high",
                "target_container_role": "main",
                "match": {"contains_any": ["keycloak", "token", "realm", "openid"]},
                "rca_hint": "IAM/Keycloak authentication path degraded",
                "recommended_actions": [
                    "Validate IAM provider health",
                    "Check realm/client configuration",
                ],
            },
        ]

    yaml = importlib.import_module("yaml")
    with rules_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload.get("rules", [])


def summarize(findings: List[Dict[str, Any]], total_events: int) -> str:
    if not findings:
        return f"Processed {total_events} log events. No known outage signatures were matched."

    categories = Counter(f["category"] for f in findings)
    category_text = ", ".join(f"{k}:{v}" for k, v in categories.items())
    return (
        f"Processed {total_events} log events and matched {len(findings)} findings "
        f"across categories -> {category_text}."
    )


def collect_actions(findings: List[Dict[str, Any]]) -> List[str]:
    actions: List[str] = []
    seen = set()
    for finding in findings:
        for action in finding.get("recommended_actions", []):
            if action not in seen:
                seen.add(action)
                actions.append(action)
    return actions


def missing_information(events: List[Dict[str, Any]], findings: List[Dict[str, Any]]) -> List[str]:
    needs: List[str] = []

    all_text = "\n".join(e.get("message", "") for e in events).lower()

    if "oom" in all_text and "limit" not in all_text:
        needs.append("Provide container memory requests/limits for affected pods.")
    if any("failedmount" in e.get("message", "").lower() for e in events):
        needs.append("Provide PVC/PV describe output and storage backend incident window.")
    if any(f.get("category") == "authentication" for f in findings):
        needs.append("Provide IAM/Keycloak realm and client error context around the incident time.")

    if not needs:
        needs.append("Provide exact incident time window, impacted namespace, and pod names for deeper RCA.")

    return needs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IFS RCA agent for local log processing.")
    parser.add_argument("--log-dir", required=True, help="Directory containing log files (.log/.txt/.jsonl)")
    parser.add_argument("--rules", default="agent/detect/rules.yaml", help="Path to rules YAML")
    parser.add_argument("--output", default="output/rca_report.md", help="Path to generated RCA markdown")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_dir = Path(args.log_dir)
    rules_path = Path(args.rules)
    output_path = Path(args.output)

    events = read_log_events(log_dir)
    rules = load_rules(rules_path)
    findings = apply_rules(events, rules)

    context = {
        "summary": summarize(findings, len(events)),
        "findings": findings,
        "actions": collect_actions(findings),
        "missing_info": missing_information(events, findings),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(context), encoding="utf-8")
    print(f"RCA report created: {output_path}")


if __name__ == "__main__":
    main()
