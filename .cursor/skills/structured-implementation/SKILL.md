---
name: structured-implementation
description: Use when implementing a PETS task with explicit scope and source-of-truth awareness.
---

# Structured Implementation

## Goal

Implement the change without drifting into unrelated cleanup or speculative rewrites.

## Workflow

1. Re-read the task objective.
2. Edit only the files that are actually authoritative for the task.
3. Keep changes small and explain non-obvious decisions in docs when needed.
4. Verify behavior or consistency after edits.
5. Update task notes and docs if the change affected project truth.

## PETS Guardrails

- no hidden architecture rewrite
- no blind donor-framework copy
- no silent shift from current runtime to roadmap architecture
