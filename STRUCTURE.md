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
- `polyphonia_runtime/`
- `index.html`
- `build_index.py`
- `assets/`
- `polyphonia.spec`

This is the executable application layer. The shipped desktop app is named **Polyphonia** (`polyphonia.exe` from `polyphonia.spec`).

### 4. Task Artifact Layer

Execution and planning artifacts live in:

- `tasks/`
- future changelogs and review docs under `docs/`

These files support work tracking and human review.

### 4.1 QA Layer (repository-local)

Quality assurance material that is **not** runtime product code lives in:

- `qa/README.md` — scope and rules for this layer
- `qa/packages/<feature>/` — versioned QA docs (test design, cases, traceability, runbooks)
- `tests/` — executable checks (`tests/e2e/` for browser-level scenarios; тематические подпакеты, например `tests/e2e/offline_scales/`)
- `.github/workflows/` — CI (например QA change gate + E2E)

Machine-generated output from local or CI runs must go to `qa/results/`, which is **gitignored** so reports and scratch files do not pollute the canonical tree.

Commit and push expectations for material changes are defined in `docs/dev-workflow/qa-change-gate.md` and enforced locally via `scripts/check_change_gate.py`.

### 5. Generated / Disposable Layer

These files are not source-of-truth:

- `build/`
- `dist/`
- `__pycache__/`
- `qa/results/` (JUnit, logs, screenshots from test runs)
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
