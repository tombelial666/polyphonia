# Documentation Standard

## Purpose

Keep project truth explicit, stable, and easy for humans and agents to follow.

## Required When Updating Docs

- separate `Confirmed`, `Assumption`, `Risk`, `Deferred`, and `Open Question` when the topic affects architecture, workflow, or product direction
- state which file is source-of-truth when generated and authored files coexist
- prefer small explicit updates over broad vague rewrites

## Required When Updating Architecture Or Workflow

Update together when relevant:

- `MANIFEST.md`
- affected docs in `docs/`
- `STRUCTURE.md` if boundaries changed
- `.cursor/` and `.claude/` guidance if agent workflow changed

## Tone

- concise
- explicit
- deterministic where possible
- no invented capabilities

## Avoid

- hiding risks
- silently turning assumptions into facts
- leaving important decisions only in chat
