"""RCA report rendering helpers (scaffold)."""

from pathlib import Path
from typing import Dict, Any


def render_markdown(context: Dict[str, Any], template_path: Path) -> str:
    """Very small fallback markdown renderer for scaffold stage."""
    _ = template_path
    summary = context.get("summary", "No summary")
    return f"# RCA Report\n\n## Summary\n{summary}\n"
