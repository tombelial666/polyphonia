from __future__ import annotations

import json
from pathlib import Path

import pytest

from riff_contract import save_riff_fragment, sessions_root, validate_riff_fragment

_ROOT = Path(__file__).resolve().parents[1]
_EXAMPLE = _ROOT / "qa" / "examples" / "riff-fragment-v0.example.json"


def test_validate_example_ok() -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    assert validate_riff_fragment(data) == []


def test_validate_missing_required_field() -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    del data["tempoBpm"]
    errs = validate_riff_fragment(data)
    assert errs
    assert any("tempoBpm" in e for e in errs)


def test_validate_tempo_out_of_range() -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    data["tempoBpm"] = 5
    errs = validate_riff_fragment(data)
    assert errs


def test_validate_extra_property_rejected() -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    data["unknownField"] = 1
    errs = validate_riff_fragment(data)
    assert errs


def test_sessions_root_creates_dir(tmp_path: Path) -> None:
    d = sessions_root(tmp_path)
    assert d.is_dir()
    assert d.name == "polyphonia_sessions"


def test_save_riff_fragment_writes_valid(tmp_path: Path) -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    path, errs = save_riff_fragment("demo-save", data, repo_root=tmp_path)
    assert errs == []
    assert path is not None
    assert path.is_file()
    assert "demo-save" in path.name


def test_save_riff_fragment_invalid_returns_none(tmp_path: Path) -> None:
    path, errs = save_riff_fragment("bad", {}, repo_root=tmp_path)
    assert path is None
    assert errs


@pytest.mark.parametrize(
    "patch",
    [
        {"meter": {"numerator": 4, "denominator": 3}},
        {"bars": [{"events": [{"beat": 0, "durationBeats": 0, "pitchClass": 0, "octave": 4}]}]},
    ],
)
def test_validate_nested_constraints(patch: dict) -> None:
    data = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    for k, v in patch.items():
        data[k] = v
    errs = validate_riff_fragment(data)
    assert errs
