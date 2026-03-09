"""Local file log collector for offline RCA analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import warnings


ALLOWED_SUFFIXES = {".log", ".txt", ".jsonl"}
TEXT_SAMPLE_SIZE = 4096
MIN_PRINTABLE_RATIO = 0.85


def _looks_like_text_file(file_path: Path) -> bool:
    """Best-effort binary detection to avoid ingesting compressed/non-text logs."""
    sample = file_path.read_bytes()[:TEXT_SAMPLE_SIZE]
    if not sample:
        return True

    # gzip magic bytes => almost certainly compressed binary content.
    if sample.startswith(b"\x1f\x8b"):
        return False

    # Embedded NULL bytes strongly indicate binary formats.
    if b"\x00" in sample:
        return False

    printable = 0
    for byte in sample:
        if byte in (9, 10, 13) or 32 <= byte <= 126:
            printable += 1

    return (printable / len(sample)) >= MIN_PRINTABLE_RATIO


def read_log_events(log_dir: Path) -> List[Dict[str, Any]]:
    """Read log lines from a directory and convert them to simple event records."""
    events: List[Dict[str, Any]] = []

    for file_path in sorted(log_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue

        if not _looks_like_text_file(file_path):
            warnings.warn(
                f"Skipping non-text or compressed log file: {file_path}",
                stacklevel=1,
            )
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
