# Test execution summary — offline scales / fretboard / chords

## Execution scope

Автоматизированная проверка офлайн-страницы гамм/аккордов через Playwright (Chromium headless) и сборку `index.html` перед каждым тестовым сеансом.

## Environment

- OS: Windows 10+ (или аналог)
- Python: 3.11+
- pytest, Playwright + Chromium

## Automated results (последний зафиксированный прогон)

| Metric | Value |
|--------|-------|
| Tests | 7 |
| Failures | 0 |

**Evidence:** локальный файл `qa/results/junit.xml` после команды из `test-execution-runbook.md` (не хранится в git).

## Дата последнего прогона

- 2026-04-23 — зелёный прогон (локально).

## Что доказано автотестами

- После `build_index.py` страница открывается по `file://` и заполняет блок гаммы для A Major.
- Подсветка root и степени гаммы на грифу соответствует ожидаемым селекторам.
- Смена лада меняет набор нот в UI.
- Клик по доступному аккорду раскрывает chord info и подсветку `in_chord`.
- Капо переносит `#capo_con` под выбранный лад и включает `has_capo`.
- Нестандартный строй `minor-third` не ломает рендер для `melodic-minor`.
- Режим бемолей отображает символ U+266D в списке нот гаммы.

## Что не доказано автотестами

- Pixel-perfect гриф.
- Полная эквивалентность `pywebview` и Chromium.
- Отсутствие сетевых запросов (TC-PETS-MANUAL-NET-01).
