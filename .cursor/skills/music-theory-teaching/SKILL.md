---
name: music-theory-teaching
description: Use when PETS needs clear, deterministic music-theory explanations with concrete examples and practice prompts.
---

# Music Theory Teaching

## Goal

Explain theory in a way that is accurate, teachable, and easy to map onto real notes, intervals, chords, scales, and instruments.

## Workflow

1. Identify the user's level and actual question.
2. State `Confirmed` context and any `Assumption`.
3. If the question is instrument-specific, apply the matching reusable instrument skill.
4. Start with the simplest correct explanation.
5. Add one concrete note-based example.
6. Call out one common confusion or exception if it materially matters.
7. End with a short practice prompt or self-check.

## Output Contract

- `Question`
- `Confirmed`
- `Assumption`
- `Explanation`
- `Example`
- `Common Mistake`
- `Practice Prompt`

## Guardrails

- do not confuse naming conventions with immutable laws
- do not hide ambiguity when theory schools differ
- do not answer beginner questions with expert-level jargon first
- prefer explicit note content over fuzzy conceptual summaries
