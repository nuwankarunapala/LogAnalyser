"""RCA report rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_markdown(context: Dict[str, Any], template_path: Path) -> str:
    """Render markdown report using a Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(default_for_string=False, default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_path.name)
    return template.render(**context)
