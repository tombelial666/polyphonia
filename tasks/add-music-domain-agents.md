# Title

Add music domain agents and skills

## Objective

Add minimal domain-specific agents and skills to the PETS AI framework for composition, music theory teaching, production guidance, solfege coaching, light orchestration, and reusable instrument-aware guidance.

## Confirmed

- PETS uses `.cursor/` as the primary adapter layer and mirrors it into `.claude/`.
- The project favors a minimal curated AI layer over heavy orchestration.
- Human review is mandatory for musical and product-facing changes.

## Assumption

- Prompt-defined specialist agents are sufficient for the first rollout.
- Domain prompts should stay advisory and reviewable rather than autonomous.
- Reusable instrument skills are better than duplicating instrument instructions inside each music agent.

## Risk

- Domain roles may overlap if prompts and skills are too vague.
- Musical advice may sound authoritative even when based on assumptions.
- Production guidance may drift into invented DAW or plugin specifics.
- Instrument advice may become noisy if each agent carries its own duplicated instrument rules.

## Deferred

- Audio-aware evaluation harnesses
- Direct DAW automation or plugin control

## Open Question

- Whether PETS should later add evaluation rubrics for musical-agent answer quality

## Source Of Truth

- `MANIFEST.md`
- `docs/dev-workflow/commands-reference.md`
- `AGENTS.md`
- `.cursor/agents/`
- `.cursor/commands/`
- `.cursor/skills/`

## Steps

- [x] Define the minimal safe rollout pattern
- [x] Add four domain agents in `.cursor/agents/`
- [x] Add paired domain skills in `.cursor/skills/`
- [x] Add orchestration-lite for multi-role music tasks
- [x] Add reusable instrument skills for music-domain work
- [x] Update workflow docs and adapter-layer indexes
- [x] Sync mirrors and verify structure

## Review Notes

- Implement the smallest viable variant now: specialist prompt roles with explicit guardrails.
- Keep orchestration light and prompt-based; defer heavy automation and audio-native workflows.
- Reuse one shared instrument-skill layer across all music agents to reduce duplication and drift.
