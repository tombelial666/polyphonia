# Task Template

## Title

## Objective

## Confirmed

- 

## Assumption

- 

## Risk

- 

## Deferred

- 

## Open Question

- 

## Source Of Truth

- Files that should be treated as authoritative for this task

## Steps

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Committed change record (QA gate)

Перед `git commit` / `git push` обновите этот блок **в момент попытки коммита** (актуальные пути и проверки):

- Дата / ветка / цель коммита:
- Пути из диффа (материальные, не `build/` и не `qa/results/`):
- Сверка с `repo-index.yaml` (добавлены ли новые `path:` при новых файлах):
- Запуск `python scripts/check_change_gate.py --staged` (перед коммитом) и/или без `--staged` перед пушем в dev:
- Ручной или автоматический смоук:

См. `docs/dev-workflow/qa-change-gate.md`.

## Review Notes

- 
