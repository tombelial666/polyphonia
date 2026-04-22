# PETS Agent Guide

This file is synchronized from `AGENTS.md` by `scripts/sync_docs.py`.

## Mission

Develop PETS as a deterministic, human-in-the-loop guitar tool with a minimal but high-signal AI workflow.

## Read First

Before planning or implementation, read:

1. `MANIFEST.md`
2. `STRUCTURE.md`
3. `docs/architecture.md`
4. `docs/desktop-transition-roadmap.md`
5. `docs/ai-foundation-bootstrap.md`

## Source Of Truth

- Canonical truth lives in `README.md`, `MANIFEST.md`, `STRUCTURE.md`, and `docs/`.
- `.cursor/` and `.claude/` are adapter layers.
- Runtime truth for execution lives in `phrygian_app.py`, `build_index.py`, `index.html`, and `assets/`.

## Safe Defaults

- Prefer minimal changes with explicit rationale.
- Do not treat saved-page artifacts as editable sources.
- Keep current `pywebview` runtime and future desktop-shell direction separate.
- Document major decisions instead of relying on memory.

## Working Mode

- Discovery when requirements are unclear
- Small technical plan before risky edits
- Human review before presenting major workflow or architecture shifts
- Docs update whenever boundaries or process assumptions change
