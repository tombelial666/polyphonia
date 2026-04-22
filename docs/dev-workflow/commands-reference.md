# PETS AI Workflow Reference

This is a minimal adapted workflow inspired by donor projects, reduced for PETS.

## Core Flow

`discover -> plan -> implement -> review -> docs`

## Commands And Intent

| Stage | Purpose | Main Output |
|---|---|---|
| `discover` | clarify a feature, workflow, or product idea | task discovery note |
| `plan` | define the smallest safe implementation path | technical task note |
| `implement` | make the change with source-of-truth awareness | code/data/docs changes |
| `review` | check correctness, risk, and documentation fit | review findings |
| `docs` | update manifest, architecture, workflow, and changelog docs | updated documentation |

## PETS-Specific Rules

- Always identify the source-of-truth file before editing.
- If a change affects project direction, update `MANIFEST.md` and related docs.
- Keep current `pywebview` runtime and desktop-shell roadmap clearly separated.
- Prefer deterministic data or explicit review over speculative automation.

## Typical Lightweight Sequence

1. Create or update a task note in `tasks/`
2. Inspect affected source files
3. Make the smallest useful change
4. Review output and update docs if needed
5. Sync adapter layers if `.cursor/` or `AGENTS.md` changed
