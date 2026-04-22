# MANIFEST

## Purpose

PETS is a guitar-focused reference and composition support project built around deterministic musical data, explicit user review, and an AI-first development workflow.

## Product Identity

- Primary current form: local static web application wrapped by a lightweight desktop shell
- Current shell: `pywebview`
- Future direction: cleaner desktop shell such as `Electron` or `Tauri`
- Product stance: human-in-the-loop tool for composers, not a one-click composition machine

## Non-Negotiable Principles

- Repository truth lives in files, not only in chat.
- Deterministic musical data beats vague automation.
- Human review is mandatory for musical and product-facing changes.
- Current runtime and future roadmap must stay explicitly separated.
- Saved-page artifacts and generated outputs must not silently replace source-of-truth files.

## Current Scope

### Confirmed

- The app currently runs by opening `index.html` through `phrygian_app.py`.
- Tuning, scale, and fretboard behavior depend on static data files in `assets/`.
- `build_index.py` is part of the current generation path for `index.html`.
- The project is being upgraded with a curated AI development layer from donor repositories.
- The AI layer may include narrow music-domain specialist agents if they stay reviewable and do not bypass human musical judgment.
- The AI layer may use a light music-direction role and reusable instrument skills, but not a heavy autonomous orchestration stack.

### Assumption

- The project can evolve toward a more maintainable desktop-shell architecture without rewriting the musical data model immediately.
- A minimal curated AI layer will deliver value faster than a full donor-framework transplant.

### Risk

- Copying too much donor infrastructure will add noise and mobile or unrelated domain rules.
- Treating generated/static outputs as authoring sources may create drift and confusion.
- Future desktop-shell planning can become speculative if not kept grounded in the current codebase.
- Music-domain agents can sound authoritative even when they are operating on assumptions or incomplete musical context.
- Too much duplicated instrument guidance across agents would increase maintenance cost and drift risk.

### Deferred

- Full Electron or Tauri implementation
- Large UI rewrite
- Automatic harmony/composition generation
- Heavy agent orchestration or complex automation stacks

### Open Question

- What the first true authoring source should become after the current static HTML phase
- Whether PETS should stay mostly static-data-driven or grow a structured app core

## AI Development Rules

- Keep the AI layer curated and minimal.
- Prefer adaptation over blind copying from donor repositories.
- Every meaningful process decision should be documented with rationale.
- Major workflow or architecture changes should update this file and affected docs together.
- Prefer narrow specialist agents with explicit inputs and outputs over monolithic music copilot prompts.
- Prefer reusable domain skills such as instrument-aware guidance over repeating the same instructions in multiple agent prompts.
