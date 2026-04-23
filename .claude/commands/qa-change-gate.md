# QA change gate review

Run a **QA change gate** review before commit or push.

## What to do

1. Read `docs/dev-workflow/qa-change-gate.md`.
2. Collect:
   - `git status`
   - `git diff --cached` (if reviewing a commit about to be made) and/or `git diff` against the dev integration base (`origin/develop` or `PETS_CHANGE_GATE_BASE`).
3. Open the relevant `tasks/*.md` and verify **Committed change record** matches the diff.
4. Cross-check every material path against `repo-index.yaml` `entries`.
5. Run `python scripts/check_change_gate.py --staged` when reviewing staged work, then `python scripts/check_change_gate.py` before push (after `git fetch`).
6. Invoke the **`qa-change-gate-reviewer`** agent persona and apply its verdict.

## Outputs

- Updated task **Committed change record** if gaps were found.
- Patches to `repo-index.yaml` when paths are missing.
- Short list of remaining **Open Question** items if dev alignment cannot be confirmed.
