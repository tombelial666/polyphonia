# STRUCTURE

## Why The Repository Is Structured This Way

PETS separates project truth, agent adapter layers, and task artifacts so the codebase can evolve without mixing runtime files, workflow files, and temporary execution output.

## Layers

### 1. Canonical Project Layer

Primary truth lives in:

- `README.md`
- `MANIFEST.md`
- `STRUCTURE.md`
- `docs/`
- `tasks/`

This layer defines identity, boundaries, workflow expectations, and roadmap.

### 2. Adapter Layer

Project-local AI adapter layers live in:

- `.cursor/`
- `.claude/`
- `AGENTS.md`
- `CLAUDE.md`

These files exist to help development tooling. They should follow canonical docs and not silently override them.

### 3. Runtime Layer

Current runnable project files:

- `phrygian_app.py`
- `index.html`
- `build_index.py`
- `assets/`
- `ChordRocks.spec`

This is the executable application layer.

### 4. Task Artifact Layer

Execution and planning artifacts live in:

- `tasks/`
- future changelogs and review docs under `docs/`

These files support work tracking and human review.

### 5. Generated / Disposable Layer

These files are not source-of-truth:

- `build/`
- `dist/`
- `__pycache__/`
- saved-page artifacts such as `A Phrygian Dominant.html` and `A Phrygian Dominant_files/`

## Boundary Rules

- `build_index.py` may define how `index.html` is assembled, but docs define how contributors should work.
- `.cursor/` and `.claude/` are workflow adapters, not product truth.
- Runtime files should not redefine project policy.
- Saved-page artifacts should not drive architecture decisions.

## Minimal Contribution Order

1. Confirm the target file is a source-of-truth file.
2. Update canonical docs if a workflow or architecture decision changes.
3. Update adapter layers if tooling guidance changed.
4. Update runtime files only after source-of-truth is clear.
