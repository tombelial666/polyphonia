from __future__ import annotations

from pathlib import Path


def test_check_change_gate_load_index_paths_multiline(monkeypatch, tmp_path: Path) -> None:
    import scripts.check_change_gate as cg

    p = tmp_path / "repo-index.yaml"
    p.write_text(
        "\n".join(
            [
                "version: 1",
                "entries:",
                "  - path: README.md",
                "  - path: docs/",
                "  - path: scripts/check_change_gate.py",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cg, "REPO_INDEX", p)
    paths = cg._load_index_paths()
    assert "README.md" in paths
    assert "docs/" in paths
    assert "scripts/check_change_gate.py" in paths

