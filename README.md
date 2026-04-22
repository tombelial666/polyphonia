# PETS

PETS is a local guitar and scale reference project built around a static web UI and a small desktop shell.

## Current State

- Runtime shell: `pywebview` via `phrygian_app.py`
- Main generated UI: `index.html`
- Source data and static assets: `assets/`
- HTML assembly script: `build_index.py`
- Packaging path: `ChordRocks.spec`

## Source Of Truth

Use these boundaries when changing the project:

1. `assets/` contains musical data, UI classes, and static resources used by the app.
2. `build_index.py` defines how `index.html` is assembled.
3. `index.html` is the runnable output used by the desktop shell.
4. `A Phrygian Dominant.html` and `A Phrygian Dominant_files/` are reference/saved-page artifacts, not core project truth.

## Development Direction

PETS is being prepared as an AI-first, human-in-the-loop guitar application for composers.

- Near term: keep the current static-web-plus-shell project usable.
- Medium term: improve maintainability, workflow, and agent support.
- Forward direction: prepare for a cleaner desktop-shell path such as `Electron` or `Tauri`.

## Project Docs

- `MANIFEST.md` - project identity, boundaries, and decision rules
- `STRUCTURE.md` - canonical docs vs adapter layers vs task artifacts
- `docs/architecture.md` - current architecture and near-term target
- `docs/desktop-transition-roadmap.md` - migration path from `pywebview` to a desktop shell
- `docs/dev-workflow/commands-reference.md` - minimal AI workflow
- `docs/ai-foundation-bootstrap.md` - donor inventory and scored decisions

## Agent Layers

- `.cursor/` - Cursor adapter layer for rules, skills, agents, and hooks
- `.claude/` - mirrored adapter layer generated from `.cursor/`
- `AGENTS.md` - concise agent-facing project guide
- `CLAUDE.md` - mirrored guide for Claude-style workflows

## Minimal Workflow

1. Clarify or discover the task.
2. Write or update a task file under `tasks/`.
3. Implement the smallest safe change.
4. Review the change with human-in-the-loop expectations.
5. Update docs when architecture, source-of-truth boundaries, or workflow change.

## Workspace

Open the project with:

- folder: `D:\Reps\PETS`
- workspace file: `D:\Reps\PETS\PETS.code-workspace`
