"""Local file log collector for offline RCA analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import warnings
import yaml


ALLOWED_SUFFIXES = {".log", ".txt", ".jsonl"}
TEXT_SAMPLE_SIZE = 4096
MIN_PRINTABLE_RATIO = 0.85
LOG_METADATA_FILE = "log_metadata.yaml"


def _load_log_metadata(log_dir: Path) -> Dict[str, Dict[str, str]]:
    """Load optional per-file metadata (display name, role overrides)."""
    metadata_path = log_dir / LOG_METADATA_FILE
    if not metadata_path.exists():
        return {}

    payload = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    files = payload.get("files", {})
    if not isinstance(files, dict):
        warnings.warn(
            f"Ignoring invalid metadata format in {metadata_path} (expected mapping under 'files').",
            stacklevel=1,
        )
        return {}

    parsed: Dict[str, Dict[str, str]] = {}
    for file_name, config in files.items():
        if not isinstance(config, dict):
            continue

        display_name = config.get("display_name")
        role = config.get("container_role")

        entry: Dict[str, str] = {}
        if isinstance(display_name, str) and display_name.strip():
            entry["display_name"] = display_name.strip()
        if isinstance(role, str) and role.strip():
            entry["container_role"] = role.strip().lower()

        if entry:
            parsed[file_name] = entry

    return parsed


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
    metadata_by_file = _load_log_metadata(log_dir)

    for file_path in sorted(log_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue

        if not _looks_like_text_file(file_path):
            warnings.warn(
                f"Skipping non-text or compressed log file: {file_path}",
                stacklevel=1,
            )
            continue

        metadata = metadata_by_file.get(file_path.name, {})
        container_role = metadata.get(
            "container_role",
            "sidecar" if "sidecar" in file_path.stem.lower() else "main",
        )
        log_name = metadata.get("display_name", file_path.name)

        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                events.append(
                    {
                        "source_file": str(file_path),
                        "log_name": log_name,
                        "line_no": line_no,
                        "message": text,
                        "container_role": container_role,
                    }
                )

    return events
