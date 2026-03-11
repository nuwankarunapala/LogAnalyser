from __future__ import annotations

from collections import Counter
from typing import Dict, List

from agent.event_model import Event


def build_timeline(events: List[Event], max_items: int = 200) -> List[Event]:
    with_ts = [e for e in events if e.timestamp is not None]
    no_ts = [e for e in events if e.timestamp is None]
    ordered = sorted(with_ts, key=lambda e: e.timestamp) + no_ts
    return ordered[:max_items]


def summarize_top_errors(events: List[Event], limit: int = 10) -> List[Dict[str, int]]:
    counter = Counter(e.matched_pattern or e.category for e in events if e.severity in {"critical", "error", "warn"})
    return [{"signal": name, "count": count} for name, count in counter.most_common(limit)]
