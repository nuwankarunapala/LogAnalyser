"""Local file log collector for offline RCA analysis."""

from pathlib import Path
from typing import List, Dict, Any


ALLOWED_SUFFIXES = {".log", ".txt", ".jsonl"}


def read_log_events(log_dir: Path) -> List[Dict[str, Any]]:
    """Read log lines from a directory and convert them to simple event records."""
    events: List[Dict[str, Any]] = []

    for file_path in sorted(log_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue

        container_role = "sidecar" if "sidecar" in file_path.stem.lower() else "main"

        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                events.append(
                    {
                        "source_file": str(file_path),
                        "line_no": line_no,
                        "message": text,
                        "container_role": container_role,
                    }
                )

    return events
