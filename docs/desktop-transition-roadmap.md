# Desktop Transition Roadmap

## Goal

Move PETS from a static-web-plus-`pywebview` runtime toward a cleaner desktop-shell architecture without forcing an immediate rewrite.

## Current State

- shell: `pywebview`
- UI entry: `index.html`
- data and behavior: `assets/`
- generation helper: `build_index.py`

## Transition Strategy

### Phase 0 - Stabilize Current Project

- clarify source-of-truth boundaries
- keep the current app runnable
- add AI workflow, docs, and task discipline

### Phase 1 - Separate Authoring From Output

- reduce direct ambiguity between authored files and generated output
- identify which parts of the UI should become true source files
- document any remaining generated step explicitly

### Phase 2 - Prepare Web Surface For Shell Migration

- define a cleaner app entry structure
- identify browser-only assumptions and shell-specific behavior
- isolate any file-path or packaging coupling

### Phase 3 - Adopt A Desktop Shell

Candidate shells:

- `Electron`
- `Tauri`

Selection criteria:

- low packaging friction
- good local file/app asset support
- reasonable bridge/API surface
- maintainable release path

## What Is Deferred

- choosing the final desktop shell now
- implementing the migration before the project truth is stabilized
- rewriting all UI behavior during the AI foundation bootstrap
