from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

ALLOWED_SUFFIXES = {".log", ".txt", ".out", ".jsonl", ".yaml", ".yml"}


@dataclass
class DiscoveredFile:
    path: Path
    source_type: str
    component: str


def _infer_source_type(path: Path, dump_folder: Path) -> str:
    rel = path.relative_to(dump_folder).as_posix().lower()
    if "/pods/descriptions" in rel:
        return "pod_description"
    if "/pods/linkerd_logs" in rel:
        return "linkerd_log"
    if "/pods/logs" in rel:
        return "pod_log"
    if "ifs-ingress/logs" in rel:
        return "ingress_log"
    if "ifs-autoscaler/logs" in rel:
        return "autoscaler_log"
    if "/deployments/descriptions" in rel:
        return "deployment_description"
    if "/jobs/descriptions" in rel:
        return "job_description"
    return "other"


def _infer_component(path: Path) -> str:
    stem = path.stem.lower()
    for token in ["db", "database", "ingress", "autoscaler", "linkerd", "projection", "integration"]:
        if token in stem:
            return token
    if path.parent.name.lower() == "logs":
        return path.stem.lower()
    return path.parent.name.lower() or path.stem.lower() or "unknown"


def discover_dump_files(dump_folder: Path) -> Dict[str, List[DiscoveredFile]]:
    categorized: Dict[str, List[DiscoveredFile]] = {}
    if not dump_folder.exists():
        return categorized

    for path in dump_folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        source_type = _infer_source_type(path, dump_folder)
        entry = DiscoveredFile(path=path, source_type=source_type, component=_infer_component(path))
        categorized.setdefault(source_type, []).append(entry)

    for files in categorized.values():
        files.sort(key=lambda f: str(f.path))
    return categorized


def flatten_discovered(discovered: Dict[str, List[DiscoveredFile]]) -> Iterable[DiscoveredFile]:
    for group in discovered.values():
        for item in group:
            yield item
