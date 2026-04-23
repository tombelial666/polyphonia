# Контракт выходов — offline scales / fretboard / chords

Документ задаёт **ожидаемые артефакты до начала работ** и где они лежат после выполнения (всё внутри репозитория PETS).

## Confirmed

- Исполняемые проверки: `tests/e2e/` (pytest + Playwright).
- Пакет документации и трассировки: `qa/packages/offline-scales-fretboard/`.
- Машинные отчёты прогона: только `qa/results/` (каталог не коммитится).

## Assumption

- Установлены Python 3.11+, `pytest`, `playwright`, браузер Chromium (`playwright install chromium` при первой ошибке).

## Risk

- `file://` и относительные `assets/` требуют, чтобы `index.html` открывался из корня PETS (так и делает `conftest`).

## Обязательные выходы

| ID | Артефакт | Путь (от корня PETS) |
|----|-----------|----------------------|
| OUT-01 | Контракт выходов | `qa/packages/offline-scales-fretboard/00-outputs-contract.md` |
| OUT-02 | Дизайн тестов | `qa/packages/offline-scales-fretboard/ai-review-test-design.md` |
| OUT-03 | Тест-кейсы | `qa/packages/offline-scales-fretboard/test-cases-comprehensive.md` |
| OUT-04 | Матрица трассировки | `qa/packages/offline-scales-fretboard/traceability-matrix.md` |
| OUT-05 | Runbook | `qa/packages/offline-scales-fretboard/test-execution-runbook.md` |
| OUT-06 | Итог прогона | `qa/packages/offline-scales-fretboard/test-execution-summary.md` |
| OUT-07 | JUnit XML (генерируется) | `qa/results/junit.xml` |
| OUT-08 | Код автотестов | `tests/e2e/offline_scales/`, `tests/e2e/support/scales_app.py`, `tests/e2e/conftest.py` |
| OUT-09 | Краткая инструкция для разработчиков | `docs/testing/offline-scales-chords-e2e.md` |

## Deferred

- Визуальные snapshot-регрессии грифа.

## Open Question

- Нужно ли в CI публиковать `qa/results/junit.xml` как артефакт job (сейчас прогон без `--junitxml` в `.github/workflows/ci.yml`).
