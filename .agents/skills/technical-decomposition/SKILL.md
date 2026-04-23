---
name: technical-decomposition
description: Use when a PETS request is understood and needs a small implementation plan before editing.
---

# Technical Decomposition

## Goal

Define the smallest safe implementation path for PETS.

## Workflow

1. Read the relevant task note if it exists.
2. Identify authoritative files for the change.
3. Split the work into a few explicit steps.
4. Note what must be verified manually or automatically.
5. Record documentation impact before implementation starts.

## PETS Guardrails

- do not blur `build_index.py`, `index.html`, and `assets/` responsibilities
- keep current `pywebview` runtime stable unless the task explicitly changes it
- treat desktop-shell ideas as roadmap unless implementation is requested
