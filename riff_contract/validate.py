from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _ROOT / "docs" / "schemas" / "riff-fragment-v0.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_riff_fragment(data: dict[str, Any]) -> list[str]:
    """Return a list of human-readable validation errors (empty if valid)."""
    v = _validator()
    return [f"{e.json_path}: {e.message}" for e in v.iter_errors(data)]
