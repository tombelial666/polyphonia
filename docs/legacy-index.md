# Legacy Index

## Purpose

This document is the full legacy map of PETS. It exists to describe the real project layout in detail, reduce agent confusion, and make source-of-truth boundaries explicit.

## Layer Model

| Layer | Status | Meaning |
|---|---|---|
| Canonical | Authoritative | Project identity, workflow, and architectural truth |
| Runtime | Authoritative for execution | Files that currently make the app run |
| Adapter | Derived-but-active | AI tooling layer used during development |
| Generated | Rebuildable | Output that can be recreated from source files |
| Reference | Informational only | Saved or historical artifacts not used by the current runtime |
| Disposable | Safe to regenerate or delete | Build caches, packaging output, and temporary artifacts |

## Root Inventory

### Version Control And Workspace

| Path | Category | Status | Description |
|---|---|---|---|
| `.git/` | version control | internal | Local git metadata for the standalone PETS repository |
| `.gitignore` | workspace control | authoritative | Excludes build output, caches, and saved-page legacy artifacts from clean working baselines |
| `PETS.code-workspace` | IDE workspace | authoritative | Cursor/VS Code workspace entry; hides `.git`, `build`, `dist`, caches, and `A Phrygian Dominant*` artifacts |

### Canonical Project Truth

| Path | Category | Status | Description |
|---|---|---|---|
| `README.md` | project overview | authoritative | Entry point for humans and agents; explains current runtime, source-of-truth rules, and project direction |
| `MANIFEST.md` | project identity | authoritative | Canonical description of PETS identity, scope, principles, risks, and AI development rules |
| `STRUCTURE.md` | repository layering | authoritative | Defines the repository layers and the difference between canonical, runtime, adapter, and generated/reference files |
| `AGENTS.md` | agent guidance | authoritative text source | Primary agent-facing guide |
| `CLAUDE.md` | agent guidance mirror | generated from `AGENTS.md` | Mirrored file for Claude-style workflows; should not be treated as the editable master |

### Runtime Entry And Packaging

| Path | Category | Status | Description |
|---|---|---|---|
| `phrygian_app.py` | runtime shell | authoritative runtime | Current desktop launcher using `pywebview`; loads local `index.html` via `file:///` |
| `build_index.py` | build helper | authoritative for current HTML assembly | Builds the current `index.html` from templates and fragments; paths are resolved relative to the repository root |
| `index.html` | runtime UI output | authoritative runtime output | Current runnable page used by `phrygian_app.py`; assembled output, not the cleanest authoring source |
| `guitar_template.html` | template source | authoritative build input | Template source used by `build_index.py` to extract note and scale selectors |
| `piano_template.html` | template source | authoritative build input | Template source used by `build_index.py` together with `_piano_html.txt` |
| `polyphonia.spec` | packaging spec | authoritative packaging path | Active PyInstaller spec for packaging `phrygian_app.py`, `index.html`, and `assets/` into **Polyphonia** (`polyphonia.exe`) |

### Canonical Documentation Tree

| Path | Category | Status | Description |
|---|---|---|---|
| `docs/architecture.md` | architecture | authoritative | Describes the current runtime and near-term target state |
| `docs/desktop-transition-roadmap.md` | roadmap | authoritative roadmap | Documents the future transition from `pywebview` to a desktop shell |
| `docs/documentation-standard.md` | doc policy | authoritative | Defines how architecture and workflow docs should be maintained |
| `docs/dev-workflow/commands-reference.md` | workflow | authoritative | Minimal AI workflow reference adapted for PETS |
| `docs/ai-foundation-bootstrap.md` | donor analysis | authoritative bootstrap record | Records donor inventory and scored decisions for the AI foundation |
| `docs/repo-index.md` | repo overview | authoritative summary | Short repo overview used as a fast index |
| `docs/legacy-index.md` | legacy overview | authoritative index | This file: the full root-and-layer legacy map |
| `docs/legacy-assets-index.md` | assets index | authoritative index | Detailed per-file index for `assets/` |
| `docs/legacy-reference-index.md` | reference/build index | authoritative index | Detailed index for `build`, `dist`, and saved-page reference artifacts |
| `docs/adr/README.md` | ADR index | authoritative | Declares ADR purpose and usage |
| `docs/adr/TEMPLATE.md` | ADR template | authoritative | Template for architecture decision records |
| `docs/templates/discovery-template.md` | task template | authoritative | Discovery template for feature clarification |
| `docs/templates/technical-decomposition-template.md` | task template | authoritative | Technical decomposition template |
| `docs/templates/code-review-template.md` | task template | authoritative | Review template |
| `docs/changelogs/README.md` | changelog policy | authoritative | Placeholder and convention for changelog notes |

### Task Layer

| Path | Category | Status | Description |
|---|---|---|---|
| `tasks/_template.md` | task template | authoritative | Default task template with `Confirmed`, `Assumption`, `Risk`, `Deferred`, and `Open Question` sections |

## Runtime Tree Summary

```text
phrygian_app.py
  -> index.html
     -> assets/*.css
     -> assets/*.js
     -> assets/_piano_html.txt (indirectly through build_index.py)

build_index.py
  -> guitar_template.html
  -> piano_template.html
  -> assets/_piano_html.txt
  -> writes index.html

polyphonia.spec
  -> phrygian_app.py
  -> index.html
  -> assets/
```

## Adapter Layer Inventory

### Cursor Layer

| Path | Category | Status | Description |
|---|---|---|---|
| `.cursor/hooks.json` | dev automation | authoritative adapter config | Post-edit hooks that trigger adapter synchronization |
| `.cursor/rules/00-project-direction.mdc` | AI rule | authoritative adapter guidance | PETS direction and boundary rules |
| `.cursor/rules/01-decision-integrity.mdc` | AI rule | authoritative adapter guidance | Explicit separation of facts, assumptions, risks, deferred items, and open questions |
| `.cursor/rules/02-docs-first.mdc` | AI rule | authoritative adapter guidance | Docs-first rule for major changes |
| `.cursor/skills/README.md` | AI index | authoritative adapter guidance | Index of curated PETS skills |
| `.cursor/skills/feature-discovery/SKILL.md` | AI skill | authoritative adapter guidance | Discovery skill |
| `.cursor/skills/technical-decomposition/SKILL.md` | AI skill | authoritative adapter guidance | Planning skill |
| `.cursor/skills/structured-implementation/SKILL.md` | AI skill | authoritative adapter guidance | Small-scope implementation skill |
| `.cursor/skills/code-review/SKILL.md` | AI skill | authoritative adapter guidance | Review skill |
| `.cursor/skills/docs-maintenance/SKILL.md` | AI skill | authoritative adapter guidance | Documentation maintenance skill |
| `.cursor/skills/desktop-shell-migration/SKILL.md` | AI skill | authoritative adapter guidance | Roadmap/planning skill for shell migration |
| `.cursor/agents/README.md` | AI index | authoritative adapter guidance | Index of curated agent roles |
| `.cursor/agents/plan-reviewer.md` | AI agent | authoritative adapter guidance | Minimal plan-review role |
| `.cursor/agents/senior-architecture-reviewer.md` | AI agent | authoritative adapter guidance | Architecture-fit reviewer |
| `.cursor/agents/docs-updater.md` | AI agent | authoritative adapter guidance | Targeted doc updater |
| `.cursor/commands/start-task.md` | AI command helper | authoritative adapter guidance | Start-task workflow helper |
| `.cursor/commands/update-docs.md` | AI command helper | authoritative adapter guidance | Update-docs workflow helper |
| `.cursor/commands/desktop-shell.md` | AI command helper | authoritative adapter guidance | Desktop-shell planning helper |

### Claude Mirror Layer

| Path | Category | Status | Description |
|---|---|---|---|
| `.claude/` | mirrored adapter tree | generated active mirror | Mirrored copy of `.cursor/` used for Claude-style workflows |
| `.claude/rules/*` | AI rule mirror | generated | Mirrored `.cursor/rules` entries |
| `.claude/skills/*` | AI skill mirror | generated | Mirrored `.cursor/skills` entries |
| `.claude/agents/*` | AI agent mirror | generated | Mirrored `.cursor/agents` entries |
| `.claude/commands/*` | AI command mirror | generated | Mirrored `.cursor/commands` entries |

### Sync Scripts

| Path | Category | Status | Description |
|---|---|---|---|
| `scripts/sync_docs.py` | dev sync utility | authoritative helper | Synchronizes `CLAUDE.md` from `AGENTS.md`; Python-based because `node` was not available in the environment |
| `scripts/sync_configs.py` | dev sync utility | authoritative helper | Synchronizes `.cursor/` into `.claude/`, intentionally skipping `hooks.json` |

## Assets And Legacy Detail

The `assets/` layer is large enough to deserve its own detailed file:

- see `docs/legacy-assets-index.md`

The reference and build layers are also split out:

- see `docs/legacy-reference-index.md`

## Legacy Trouble Spots

### Confirmed

- Older local trees may still contain a `build/ChordRocks/` cache from a former spec filename; current builds use `build/polyphonia/`.
- `index.html` is the active runtime output, but not the cleanest authoring source.
- `assets/` contains mostly minified JavaScript and CSS without an obvious upstream unminified source tree in this repository.
- `.cursor/` is the primary adapter layer; `.claude/` is a generated mirror.

### Risk

- Agents may edit `index.html` directly even when the safer change belongs in `build_index.py`, a template, or `assets/`.
- The presence of saved-page artifacts can cause agents to treat the wrong HTML and JS bundle as authoritative.
- Double-maintained instrument data may drift if changes are made in only one place.

### Open Question

- Which files should become the future clean web-authoring source when PETS moves away from the current mixed generated/runtime arrangement?
