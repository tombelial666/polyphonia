# Tests (`tests/`)

## Layout

| Путь | Назначение |
|------|------------|
| `tests/e2e/` | Браузерные сценарии (Playwright + pytest). |
| `tests/e2e/offline_scales/` | Атомарные E2E по офлайн-странице гамм/грифа (маркер `e2e`). |
| `tests/e2e/support/` | Общие хелперы (например `ScalesApp`). |
| `tests/conftest.py` | Корневой pytest; маркеры в `pytest.ini`. |
| (будущее) `tests/unit/` | Быстрые юнит-тесты без браузера, если появятся. |

## Документация и планы

- Архитектура QA-слоя репозитория: `qa/README.md`.
- Пакет по офлайн-гаммам/грифу: `qa/packages/offline-scales-fretboard/`.
- Краткая инструкция для разработчиков: `docs/testing/offline-scales-chords-e2e.md`.
