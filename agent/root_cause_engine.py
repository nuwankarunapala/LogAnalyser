from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from agent.event_model import Event

BASE_SEVERITY = {"critical": 5, "error": 4, "warn": 2, "info": 1}


def score_root_causes(events: List[Event]) -> List[Dict[str, object]]:
    buckets: Dict[str, Dict[str, object]] = defaultdict(lambda: {
        "category": "unknown",
        "score": 0,
        "count": 0,
        "components": set(),
        "evidence": [],
    })

    for event in events:
        category = event.category or "unknown"
        bucket = buckets[category]
        bucket["category"] = category
        bucket["count"] += 1
        bucket["score"] += BASE_SEVERITY.get(event.severity, 1)
        bucket["components"].add(event.component)
        if event.matched_pattern and len(bucket["evidence"]) < 5:
            bucket["evidence"].append({
                "timestamp": event.timestamp.isoformat() if event.timestamp else "N/A",
                "source": event.source_file,
                "message": event.message,
                "pattern": event.matched_pattern,
            })

    ranked = []
    for data in buckets.values():
        comp_count = len(data["components"])
        score = int(data["score"]) + comp_count * 2
        ranked.append({
            "category": data["category"],
            "score": score,
            "count": data["count"],
            "components": sorted(data["components"]),
            "confidence": min(95, 30 + score),
            "evidence": data["evidence"],
        })

    return sorted(ranked, key=lambda item: item["score"], reverse=True)
