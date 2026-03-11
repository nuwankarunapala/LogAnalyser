from pathlib import Path

from agent.file_discovery import discover_dump_files


def test_discovery_categorizes_known_paths(tmp_path: Path) -> None:
    file_path = tmp_path / "IFS_Cloud" / "pods" / "logs" / "a.log"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("hello", encoding="utf-8")

    discovered = discover_dump_files(tmp_path)
    assert "pod_log" in discovered
    assert discovered["pod_log"][0].path == file_path
