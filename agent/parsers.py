from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from agent.event_model import Event
from agent.file_discovery import DiscoveredFile

TS_PATTERNS = [
    re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"),
    re.compile(r"(?P<ts>\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})"),
]

SEVERITY_TOKENS = {
    "critical": ["critical", "panic", "fatal"],
    "error": ["error", "exception", "ora-", "failed"],
    "warn": ["warn", "warning", "timeout", "back-off"],
    "info": ["info", "started", "ready"],
}


def parse_timestamp(text: str) -> Optional[datetime]:
    for pattern in TS_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group("ts").replace(",", ".")
        raw = raw.replace("Z", "+00:00")
        for fmt in [None, "%Y/%m/%d %H:%M:%S"]:
            try:
                return datetime.fromisoformat(raw) if fmt is None else datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def detect_severity(line: str) -> str:
    lowered = line.lower()
    for severity, tokens in SEVERITY_TOKENS.items():
        if any(token in lowered for token in tokens):
            return severity
    return "info"


def match_pattern(line: str, patterns: List[Dict[str, str]]) -> Tuple[Optional[str], str]:
    lowered = line.lower()
    for pattern in patterns:
        tokens = [t.lower() for t in pattern.get("contains_any", [])]
        if tokens and any(token in lowered for token in tokens):
            return pattern.get("name"), pattern.get("category", "unknown")
    return None, "unknown"


def parse_discovered_file(discovered: DiscoveredFile, patterns: List[Dict[str, str]]) -> Iterable[Event]:
    with discovered.path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            matched_pattern, category = match_pattern(line, patterns)
            yield Event(
                timestamp=parse_timestamp(line),
                source_file=str(discovered.path),
                source_type=discovered.source_type,
                component=discovered.component,
                severity=detect_severity(line),
                message=line[:800],
                matched_pattern=matched_pattern,
                category=category,
                raw_line=line,
                line_no=line_no,
            )


def filter_window(
    events: List[Event],
    outage_start: datetime,
    window_minutes: int,
    keep_related_without_timestamp: bool = True,
) -> List[Event]:
    from datetime import timedelta

    start = outage_start - timedelta(minutes=window_minutes)
    end = outage_start + timedelta(minutes=window_minutes)
    filtered: List[Event] = []
    for event in events:
        if event.timestamp and start <= event.timestamp <= end:
            filtered.append(event)
        elif keep_related_without_timestamp and event.matched_pattern:
            filtered.append(event)
    return filtered
