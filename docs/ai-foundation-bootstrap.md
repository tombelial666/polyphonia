# AI Foundation Bootstrap

## Donor Inventory

## Confirmed

### From `D:\DevReps\MobileLiteApp`

Kept as inspiration or adapted source:

- workflow idea: discovery -> planning -> implementation -> review -> docs
- `.cursor` + `.claude` adapter pairing
- hook pattern for syncing adapter layers and agent-facing docs
- curated skills and agent roles

Excluded from direct carry-over:

- React Native / Expo stack rules
- mobile UI planning specifics
- design token and localization rules tied to that product
- mobile-only test commands and architecture constraints

### From `C:\ai-framework-reaper`

Kept as inspiration or adapted source:

- decision integrity pattern
- docs-first discipline
- docs maintenance skill mindset

Excluded from direct carry-over:

- REAPER-first and music-ingestion-specific rules
- FL Studio / SD3 workflows
- domain commands and skills

### From `D:\DevReps\aiqa`

Kept as inspiration or adapted source:

- canonical truth inside repo
- adapter-layer framing
- structure discipline for truth vs execution artifacts

Excluded from direct carry-over:

- cross-repo impact analysis domain
- external workspace path assumptions
- legacy runtime adapter references

## Decision Scorecard

Scoring model:

- each criterion is scored from `0` to `12`
- higher is better
- criteria are:
  1. Product fit
  2. Current codebase fit
  3. Human-in-the-loop value
  4. AI workflow usefulness
  5. Simplicity of rollout
  6. Maintenance cost efficiency
  7. Risk containment
  8. Future desktop-shell leverage

## Decision 1 - Use A Minimal Curated AI Layer

**Decision**: adopt only the highest-signal AI workflow pieces instead of copying donor frameworks wholesale.

**Why**: PETS is small and mixed-source; a full transplant would create more policy than product value.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 11 | Keeps PETS focused on guitar/composer workflow |
| Current codebase fit | 10 | Matches the small current project shape |
| Human-in-the-loop value | 11 | Promotes explicit review without heavy automation |
| AI workflow usefulness | 9 | Enough structure to guide agents well |
| Simplicity of rollout | 11 | Small number of files and concepts |
| Maintenance cost efficiency | 10 | Less inherited noise to maintain |
| Risk containment | 12 | Avoids donor-specific sprawl |
| Future desktop-shell leverage | 8 | Good enough foundation, even if not exhaustive |
| **Total** | **82/96** | Strong default choice |

## Decision 2 - Keep Canonical Truth In Repo Docs

**Decision**: use `MANIFEST.md`, `STRUCTURE.md`, `README.md`, and `docs/` as canonical truth.

**Why**: current PETS mixes runtime, generated output, and static data; explicit truth files reduce drift.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 10 | Supports a long-lived project identity |
| Current codebase fit | 9 | Needed because sources are mixed today |
| Human-in-the-loop value | 11 | Humans can verify decisions in files |
| AI workflow usefulness | 11 | Gives agents stable references |
| Simplicity of rollout | 9 | Requires only a few docs |
| Maintenance cost efficiency | 10 | Prevents repeated rediscovery |
| Risk containment | 12 | Reduces silent architecture drift |
| Future desktop-shell leverage | 9 | Helps migration planning later |
| **Total** | **81/96** | High-value structural decision |

## Decision 3 - Use `.cursor` As Primary Adapter Layer And Mirror To `.claude`

**Decision**: keep active adapter files in `.cursor` and mirror them into `.claude` with simple sync scripts.

**Why**: this preserves cross-tool compatibility while avoiding two independently edited tool layers.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 8 | Mostly workflow infrastructure, not product logic |
| Current codebase fit | 9 | Small enough to add now |
| Human-in-the-loop value | 8 | Helps tool consistency, indirectly helps humans |
| AI workflow usefulness | 11 | Makes guidance reusable across tools |
| Simplicity of rollout | 8 | Slightly more setup because mirroring is needed |
| Maintenance cost efficiency | 9 | Better than manual double-editing |
| Risk containment | 9 | Limits divergence between tool layers |
| Future desktop-shell leverage | 7 | Workflow benefit more than runtime benefit |
| **Total** | **69/96** | Worth doing in minimal form |

## Decision 4 - Preserve `pywebview`, But Document `Electron/Tauri` As Roadmap

**Decision**: keep the current runnable shell untouched while documenting desktop-shell migration as a future path.

**Why**: the user wants lower risk now, and the current app already runs.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 10 | Respects current working project |
| Current codebase fit | 12 | Zero forced rewrite right now |
| Human-in-the-loop value | 9 | Easier for humans to verify current behavior |
| AI workflow usefulness | 8 | Gives agents a clear present-vs-future split |
| Simplicity of rollout | 12 | Minimal risk decision |
| Maintenance cost efficiency | 9 | Avoids expensive early migration |
| Risk containment | 12 | Prevents speculative rebuild |
| Future desktop-shell leverage | 10 | Roadmap keeps the future open |
| **Total** | **82/96** | Best low-risk technical posture |

## Decision 5 - Adopt A Minimal Task Workflow

**Decision**: adapt a small workflow of discovery, plan, implementation, review, and docs.

**Why**: PETS needs just enough process to support agents, not a full enterprise workflow.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 10 | Helps a growing tool project |
| Current codebase fit | 9 | Works without requiring a large app architecture |
| Human-in-the-loop value | 12 | Review remains built in |
| AI workflow usefulness | 11 | Gives agents a predictable path |
| Simplicity of rollout | 10 | Can be expressed with a few docs and templates |
| Maintenance cost efficiency | 9 | Light but useful |
| Risk containment | 10 | Reduces ad hoc changes |
| Future desktop-shell leverage | 8 | Scales into larger tasks later |
| **Total** | **79/96** | Good minimal process layer |

## Decision 6 - Ignore Saved-Page Artifacts In The Clean Project Baseline

**Decision**: treat `A Phrygian Dominant.html`, `A Phrygian Dominant_files/`, and similar saved-page artifacts as non-core files.

**Why**: they are reference leftovers, not the working runtime path.

| Criterion | Score | Notes |
|-----------|------:|-------|
| Product fit | 9 | Keeps the repository about the actual app |
| Current codebase fit | 10 | Matches observed structure |
| Human-in-the-loop value | 8 | Reduces confusion during review |
| AI workflow usefulness | 10 | Prevents agents from treating noise as truth |
| Simplicity of rollout | 12 | Easy cleanup boundary |
| Maintenance cost efficiency | 11 | Less duplicate junk to manage |
| Risk containment | 11 | Lowers accidental edits in wrong files |
| Future desktop-shell leverage | 6 | Indirect benefit only |
| **Total** | **77/96** | Strong cleanup boundary |
