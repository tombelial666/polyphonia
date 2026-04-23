# Task: Remember Mode Session

## Title

Добавить сохранение режима (online/offline) между сессиями через checkbox «Запомнить»

## Objective

Пользователь, переключившийся в Assist-режим, может поставить галочку «Запомнить» в настройках, и при следующем открытии приложение восстановит режим автоматически — без необходимости переключаться каждый раз.

## Confirmed

- Источник истины UI: `build_index.py` (генерирует `index.html`); редактировать нужно только `build_index.py`, а не `index.html` напрямую.
- Логика режима живёт в `assets/polyphonia_ui.js` (`getPolyMode`, `applyPolyModeRuntime`, `boot`).
- Хранение: `localStorage` ключ `polyphonia_poly_mode` — согласован с остальными `STORAGE_*` константами файла.
- Новые E2E-тесты TC-SET-005/006/007 добавлены в `tests/e2e/offline_scales/test_polyphonia_assist.py` и прошли (16/16).
- QA-кейсы зарегистрированы в `qa/packages/polyphonia-ux-ai-framework/test-cases.md`.
- Все затронутые пути уже присутствуют в `repo-index.yaml`; новых entries не требуется.

## Assumption

- Без `pywebview` (браузер напрямую) восстановление режима работает через URL-hash и CSS-класс; Python `set_poly_mode` не вызывается — это нормально.
- Пользователь понимает, что `POLYPHONIA_MODE` env-переменная имеет приоритет над localStorage при холодном старте Python-процесса.

## Risk

- Если Python стартует в offline (по `POLYPHONIA_MODE=offline`), а localStorage говорит assist — JS применит assist, но Python-бэкенд уже в offline. Практически это работает: `set_poly_mode` меняет `_ui_mode` в рантайме.
- `localStorage` очищается при сбросе данных браузера/WebView; пользователь может потерять настройку.

## Deferred

- Синхронизация сохранённого режима с `polyphonia_sessions/auth.json` (auth.json уже хранит API-ключи с "remember me" — можно было бы объединить, но не нужно сейчас).

## Open Question

- Нужно ли показывать badge/индикатор в шапке, что режим «запомнен»?

## Source Of Truth

- `build_index.py` — источник HTML-структуры настроек
- `assets/polyphonia_ui.js` — вся логика переключения режима
- `qa/packages/polyphonia-ux-ai-framework/test-cases.md` — тест-кейсы TC-SET-005..007

## Steps

- [x] Добавить checkbox `#settings_poly_mode_remember` в `build_index.py`
- [x] Добавить `STORAGE_POLY_MODE`, `syncPolyModeRememberCheckbox`, `restorePolyModeFromStorage` в `polyphonia_ui.js`
- [x] Обновить `applyPolyModeRuntime` — сохранять/очищать при применении режима
- [x] Добавить обработчик чекбокса в `initSettingsHandlers`
- [x] Вызвать `restorePolyModeFromStorage()` в `boot()`
- [x] Регенерировать `index.html` через `python build_index.py`
- [x] Добавить TC-SET-005/006/007 в QA-документацию
- [x] Написать и прогнать E2E-тесты (16/16 passed)

## Committed change record (QA gate)

- 2026-04-24 / codex/refactor-runtime-boundaries / prepare commit and push through QA gate: обновлён `repo-index.yaml` для новых файлов в `.agents/skills/` и `scripts/clean_chrome_bookmarks.py`; проверены актуальные task-заметки и тесты.
- Пути из диффа (материальные):
  - `build_index.py`
  - `assets/polyphonia_ui.js`
  - `index.html` (сгенерирован)
  - `tests/e2e/offline_scales/test_polyphonia_assist.py`
  - `qa/packages/polyphonia-ux-ai-framework/test-cases.md`
  - `tasks/remember-mode-session.md`
  - `.agents/skills/*`
  - `scripts/clean_chrome_bookmarks.py`
- Сверка с `repo-index.yaml`: все пути теперь покрыты существующими entries (проверено).
- Запуск `python scripts/check_change_gate.py --staged`: успешен перед коммитом.
- Смоук: `python -m pytest tests/e2e/offline_scales/test_polyphonia_assist.py -q` → 16 passed.

## Review Notes

- `index.html` редактировать нельзя напрямую — только через `build_index.py`, иначе при следующей сборке изменения потеряются. Это задокументировано в этой задаче.
