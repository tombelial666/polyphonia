"""
PETS change gate: diff vs repo-index.yaml and tasks/ presence.

Usage:
  python scripts/check_change_gate.py
  python scripts/check_change_gate.py --base origin/develop
  python scripts/check_change_gate.py --allow-no-task   # emergency override

Environment:
  PETS_CHANGE_GATE_BASE - default merge base ref if --base omitted
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_INDEX = ROOT / "repo-index.yaml"
PATH_LINE = re.compile(r"^\s*-\s*path:\s*(.+?)\s*$", re.MULTILINE)

EXEMPT_PREFIXES = (
    "build/",
    "dist/",
    "qa/results/",
    ".pytest_cache/",
    "__pycache__/",
)

MIRROR_ONLY_PREFIXES = (".claude/",)
MIRROR_ONLY_FILES = frozenset({"CLAUDE.md"})


def _material_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if not _is_exempt(p)]


def _is_mirror_only_material(paths: list[str]) -> bool:
    if not paths:
        return False
    for p in paths:
        pn = _norm(p)
        if pn in MIRROR_ONLY_FILES:
            continue
        if any(pn.startswith(prefix) for prefix in MIRROR_ONLY_PREFIXES):
            continue
        return False
    return True


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip()


def _load_index_paths() -> list[str]:
    text = REPO_INDEX.read_text(encoding="utf-8")
    return [_norm(m.group(1)) for m in PATH_LINE.finditer(text)]


def _indexed(path: str, index_paths: list[str]) -> bool:
    p = _norm(path)
    for raw in index_paths:
        entry = _norm(raw)
        if p == entry:
            return True
        if entry.endswith("/") and p.startswith(entry):
            return True
        if not entry.endswith("/") and p.startswith(entry + "/"):
            return True
    return False


def _git_merge_base(base: str) -> str | None:
    r = subprocess.run(
        ["git", "merge-base", "HEAD", base],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def _git_changed_since(since: str) -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--name-only", since, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        sys.exit(2)
    return [_norm(x) for x in r.stdout.splitlines() if x.strip()]


def _default_base() -> str:
    env = __import__("os").environ.get("PETS_CHANGE_GATE_BASE", "").strip()
    if env:
        return env
    for candidate in ("origin/develop", "origin/main", "origin/dev"):
        chk = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=ROOT,
            capture_output=True,
        )
        if chk.returncode == 0:
            return candidate
    return "HEAD~1"


def _is_exempt(path: str) -> bool:
    p = _norm(path)
    return any(p == ep.rstrip("/") or p.startswith(ep) for ep in EXEMPT_PREFIXES)


def _needs_task(material: list[str]) -> bool:
    if not material:
        return False
    if _is_mirror_only_material(material):
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="PETS QA change gate checks")
    ap.add_argument("--base", default="", help="Merge base ref (default: PETS_CHANGE_GATE_BASE or origin/develop/...)")
    ap.add_argument("--allow-no-task", action="store_true", help="Do not require tasks/ in diff")
    ap.add_argument(
        "--staged",
        action="store_true",
        help="Use staged files (git diff --cached) instead of merge-base..HEAD",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    since = ""
    if args.staged:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            sys.exit(2)
        changed = [_norm(x) for x in r.stdout.splitlines() if x.strip()]
    else:
        base = args.base or _default_base()
        mb = _git_merge_base(base)
        if mb is None:
            print(
                f"WARN: no merge-base with {base!r}; falling back to diff {base}...HEAD",
                file=sys.stderr,
            )
            since = base
        else:
            since = mb
        changed = _git_changed_since(since)
    if args.verbose:
        if args.staged:
            print("mode=staged (git diff --cached)")
        else:
            print(f"mode=range since={since}")
        for c in changed:
            print(f"  {c}")

    if not changed:
        print("OK: empty diff")
        return 0

    material = _material_paths(changed)
    if not material:
        print("OK: only exempt paths")
        return 0

    index_paths = _load_index_paths()
    unindexed = [p for p in material if not _indexed(p, index_paths)]
    if unindexed:
        print("FAIL: paths not covered by repo-index.yaml:", file=sys.stderr)
        for p in unindexed:
            print(f"  {p}", file=sys.stderr)
        print("Update repo-index.yaml entries or fix paths.", file=sys.stderr)
        return 1

    if _needs_task(material) and not args.allow_no_task:
        if not any(p.startswith("tasks/") for p in changed):
            print(
                "FAIL: material changes require an updated task file under tasks/",
                file=sys.stderr,
            )
            print("Update tasks/<your-task>.md (Committed change record) or pass --allow-no-task.", file=sys.stderr)
            return 1

    if any(p == "repo-index.yaml" for p in changed):
        print(
            "NOTE: repo-index.yaml changed — ensure index matches what you intend to land in dev.",
        )

    print("OK: change gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
