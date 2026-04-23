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
6. `docs/legacy-index.md`
7. `docs/legacy-assets-index.md`
8. `docs/legacy-reference-index.md`
9. `repo-index.yaml`
10. `impact-map.yaml`
11. `docs/dev-workflow/qa-change-gate.md`

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

## QA change gate

Before **`git commit`** or **`git push`** to the dev integration branch:

- Update the **Committed change record** in the relevant `tasks/*.md` for every **material** code or truth change.
- Keep `repo-index.yaml` aligned with the paths that ship; run `python scripts/check_change_gate.py --staged` before commit and the non-staged script before push (see `docs/dev-workflow/qa-change-gate.md`).
- Use the **`qa-change-gate-reviewer`** agent (`.cursor/commands/qa-change-gate.md`) when the diff is non-trivial.

Treat **dev deployment parity** as **Confirmed** only with explicit evidence; otherwise mark **Assumption** or **Open Question**.

## Domain Specialists

- Use narrow domain specialists for composition support, theory teaching, production guidance, and solfege coaching when that is more useful than a generic assistant.
- Use `music-director` for mixed music tasks that need light routing across specialist roles.
- Reuse shared instrument-aware skills instead of duplicating guitar, piano, bass, drums, strings, or voice rules inside every music agent.
- Keep domain outputs reviewable by separating `Confirmed`, `Assumption`, `Risk`, and `Open Question` where applicable.
- Do not present stylistic guesses, production certainty, or musical preference as verified fact.
