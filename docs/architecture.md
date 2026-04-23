# Architecture

## Current Runtime

PETS currently runs as a local desktop wrapper around a generated static web page.

### Current Execution Path

1. `phrygian_app.py` launches `pywebview`
2. `pywebview` opens local `index.html`
3. `index.html` loads data and UI logic from `assets/`
4. fretboard and scale behavior are driven by deterministic JavaScript data
5. optional frozen desktop build: `polyphonia.spec` produces **Polyphonia** (`polyphonia.exe`) while the repository remains PETS

Small Python runtime helpers may be extracted under `polyphonia_runtime/` as long as `phrygian_app.py -> index.html -> assets/` remains the stable execution path.

## Current Authoring Reality

The codebase has mixed authoring and generated characteristics:

- `assets/` contains real project data and logic
- `build_index.py` participates in generating the runnable page
- `index.html` is a runnable artifact that may also still need direct inspection

Because of this mixed state, contributors must document which file is being treated as authoritative for a change.

## AI-First Development Architecture

PETS uses a minimal in-repo AI layer:

- canonical docs define truth
- `.cursor/` contains active Cursor guidance
- `.claude/` mirrors the active guidance
- `tasks/` captures discovery, plans, implementation notes, and review artifacts

## Current Boundaries

### Confirmed

- `pywebview` is the active shell
- static HTML and asset files are the active UI delivery path
- the AI layer is intentionally minimal and curated

### Assumption

- a future desktop shell should consume a cleaner web app surface than the current generated file path

### Risk

- mixing generated and authored files can blur source-of-truth boundaries

### Deferred

- full app-shell migration
- structured frontend build system
- advanced plugin or extension architecture

## Assist and Shell Bridge (Experimental)

### Confirmed

- The generated page may expose a small `window.polyphonia` object for reviewable assist flows, deterministic exports (for example MusicXML snapshots), and optional native hooks such as fullscreen when running under `pywebview` with `js_api`.
- Assist output is not treated as canonical musical truth; it must remain separable from deterministic `assets/` scale and chord data.

### Assumption

- A future desktop shell can reuse the same bridge names without changing the data layer first.

### Risk

- Any feature that merges chat output into saved project state without an explicit artifact and review step can reintroduce configuration drift.

## Near-Term Target

The near-term target is not a full rewrite. It is a cleaner project foundation that supports:

- safer edits
- clearer project truth
- better human review
- future extraction of the web layer into a desktop-shell-friendly app structure
