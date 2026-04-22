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

## Specialist Domain Roles

PETS can use narrow music-domain specialists inside the same minimal AI framework:

- `music-director` for mixed or cross-domain music tasks
- `composer` for constrained composition options
- `music-theory-teacher` for theory explanation and examples
- `producer` for arrangement and production direction
- `solfege-teacher` for graded ear-training and sight-singing drills

These specialists can share reusable instrument-aware skills:

- `guitar-guidance`
- `piano-guidance`
- `bass-guidance`
- `drums-guidance`
- `strings-guidance`
- `voice-guidance`

These specialists should:

- work from explicit inputs and say what is assumed
- return reviewable options rather than overconfident final answers
- avoid claiming audio certainty, authorship guarantees, or unverifiable stylistic facts

## Implementation Variants

### Variant A - Specialist Prompt Library

Use separate prompt roles plus paired skills for each musical job. This is the current PETS default because it keeps rollout simple, reviewable, and aligned with the existing minimal adapter layer.

### Variant B - Conductor Plus Specialists

Add a coordinator that routes work to the right specialist and merges results. PETS now supports a lightweight prompt-level version of this through `music-director`, but not a heavy autonomous orchestration stack.

### Variant C - Evaluation-Backed Specialists

Keep the specialist roles, but add reusable rubrics, example prompts, and regression checks for musical quality and honesty. This is the strongest long-term pattern, but not the lightest first rollout.

## Music Command Shortcuts

The adapter layer can expose focused helper commands for common music tasks:

- `music-task` for orchestration-lite across specialists
- `compose-idea` for composition support
- `theory-lesson` for theory explanation
- `production-pass` for arrangement and production feedback
- `solfege-drill` for ear-training and sight-singing exercises

## Typical Lightweight Sequence

1. Create or update a task note in `tasks/`
2. Inspect affected source files
3. Use `music-director` when a music task spans multiple specialist viewpoints
4. Apply a specialist role if the task benefits from narrow domain expertise
5. Pull in a reusable instrument skill if voicing, range, fingering, or playability matters
6. Make the smallest useful change
7. Review output and update docs if needed
8. Sync adapter layers if `.cursor/` or `AGENTS.md` changed
