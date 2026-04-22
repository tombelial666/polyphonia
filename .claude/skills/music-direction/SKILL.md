---
name: music-direction
description: Use when a PETS music task spans composition, theory, production, or training and needs light orchestration rather than a monolithic answer.
---

# Music Direction

## Goal

Provide orchestration-lite for musical tasks by identifying the primary specialist lens, pulling in only the supporting lenses that matter, and returning one integrated recommendation.

## Workflow

1. Classify the brief as composition, theory, production, solfege, or mixed.
2. Separate `Confirmed` inputs from `Assumption`.
3. Name the primary specialist role.
4. Add only the supporting specialists that materially improve the answer.
5. If an instrument is central, apply the matching reusable instrument skill.
6. Synthesize one recommendation with explicit tradeoffs.
7. End with a next-best prompt the user can run next.

## Output Contract

- `Task Type`
- `Confirmed`
- `Assumption`
- `Primary Specialist`
- `Supporting Specialists`
- `Integrated Recommendation`
- `Risk`
- `Next Best Prompt`

## Guardrails

- do not pretend an automated conductor runtime already exists
- do not include every specialist by default
- do not flatten real tradeoffs into false certainty
- keep the answer compact and reviewable
