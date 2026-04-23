# QA change gate — adapter and canonical workflow

## Objective

Ввести постоянное сопровождение изменений кода через QA-гейт: дифф ↔ `tasks/` ↔ `repo-index.yaml` ↔ ожидания dev-ветки.

## Confirmed

- Каноническая процедура: `docs/dev-workflow/qa-change-gate.md`.
- Скрипт проверки: `scripts/check_change_gate.py`.
- Агент и команда Cursor: `qa-change-gate-reviewer`, `.cursor/commands/qa-change-gate.md`.
- Правило репозитория: `.cursor/rules/04-qa-change-gate.mdc`.
- Индекс обновлён: `repo-index.yaml` включает `impact-map.yaml`, самоиндексацию, `qa/`, `tests/`, `pytest.ini`, `requirements-dev.txt`, скрипт гейта и док процедуры.
- CI: `.github/workflows/ci.yml` — job `change-gate` и зависимый от него `e2e` на Ubuntu.

## Assumption

- База сравнения с dev по умолчанию: `origin/develop` (или `PETS_CHANGE_GATE_BASE`); в GitHub Actions для PR база берётся из `github.base_ref`.

## Risk

- Скрипт смотрит на **коммитный** диапазон; перед локальным коммитом нужен режим `--staged`.
- На self-hosted или не-GitHub хостинге этот workflow не выполняется — гейт остаётся локальным/другим CI.

## Committed change record

- **2026-04-23 (планируемый коммит):** добавлены `docs/dev-workflow/qa-change-gate.md`, `scripts/check_change_gate.py`, `.cursor/rules/04-qa-change-gate.mdc`, `.cursor/agents/qa-change-gate-reviewer.md`, `.cursor/commands/qa-change-gate.md`; обновлены `AGENTS.md`, `STRUCTURE.md`, `docs/dev-workflow/commands-reference.md`, `repo-index.yaml`, `tasks/_template.md`, `tasks/qa-change-gate.md`, `.cursor/agents/README.md`.
- **2026-04-23 (roadmap в репо):** добавлен `tasks/polyphonia-modernization-roadmap.md`; обновлены `repo-index.yaml`, `docs/repo-index.md`.
- **2026-04-23 (Polyphonia packaging):** `ChordRocks.spec` удалён; добавлен `polyphonia.spec` (exe `polyphonia`); имя приложения в UI и окне — **Polyphonia**; обновлены `README.md`, `MANIFEST.md`, `STRUCTURE.md`, `repo-index.yaml`, `impact-map.yaml`, `docs/repo-index.md`, `docs/legacy-index.md`, `docs/legacy-reference-index.md`, `phrygian_app.py`, `build_index.py`, `index.html`.
- **2026-04-23 (CI + E2E структура):** `.github/workflows/ci.yml`; перенос путей в `build_index.py` относительно корня репозитория; разбиение E2E на `tests/e2e/offline_scales/`, `tests/e2e/support/scales_app.py`, корневые `tests/conftest.py` и пакетные `__init__.py`; маркер `e2e` в `pytest.ini`; обновлены `MANIFEST.md`, `docs/dev-workflow/qa-change-gate.md`, `docs/dev-workflow/commands-reference.md`, `docs/testing/offline-scales-chords-e2e.md`, `tests/README.md`, QA-пакет offline-scales-fretboard, `tasks/fix-fretboard-render.md`, `repo-index.yaml`.
- **2026-04-24 (commands-reference cheat sheet):** расширен блок «Polyphonia и репозиторий — шпаргалка терминала» в `docs/dev-workflow/commands-reference.md`.
- **2026-04-24 (POLYPHONIA_MODE + operator token):** `phrygian_app.py` (выбор режима, `PolyphoniaApi(ui_mode)`), `assets/polyphonia_ui.js`, `build_index.py`, `tests/e2e/conftest.py` (`?poly_mode=assist`), `scripts/repo_admin_cli.py` (`PETS_OPERATOR_TOKEN`), `tests/test_phrygian_startup_mode.py`, обновлены dev-notes и `assist-variant-decision.md`.
- **2026-04-24 (repo admin CLI):** `scripts/repo_admin_cli.py`, `scripts/__init__.py`, `docs/dev-notes/repo-admin-cli.md`, `tests/test_repo_admin_cli.py`, `docs/dev-workflow/commands-reference.md`, `docs/repo-index.md`, `repo-index.yaml`.
- **2026-04-24 (Assist OpenAI bridge):** `phrygian_app.py` (`openai_chat`, `set_openai_api_key`), панель Assist в `build_index.py` / `assets/polyphonia_ui.js`, `docs/dev-notes/openai-assist-bridge.md`, `tasks/assist-variant-decision.md`, `repo-index.yaml`, e2e `test_assist_openai_status_without_pywebview`.
- **2026-04-24 (Assist dialog Markdown + настройки UI):** `phrygian_app.py` (`append_assist_dialog_md`, `assist_dialogs_dir`), карточка «Настройки» и модалка в `build_index.py` / `index.html`, `assets/polyphonia_ui.js`, `docs/dev-notes/openai-assist-bridge.md`, `docs/dev-workflow/commands-reference.md`, `tests/test_phrygian_dialog_md.py`, e2e `test_polyphonia_settings_modal`.
- **2026-04-24 (Claude Code terminal launcher):** `scripts/claude_terminal.py`, `docs/dev-notes/claude-terminal-launcher.md`, `docs/dev-workflow/commands-reference.md`, `tests/test_claude_terminal_launcher.py`, `repo-index.yaml`.
- **2026-04-24 (Assist LLM connection UX):** `phrygian_app.py` (`get_openai_connection`, `openai_ping`), `assets/polyphonia_ui.js`, `build_index.py` / `index.html`, `docs/dev-notes/openai-assist-bridge.md`, `docs/dev-notes/assist-llm-login-ux.md`, `docs/repo-index.md`, `tests/test_phrygian_openai_connection.py`, e2e `test_polyphonia_settings_modal`, `repo-index.yaml`.
- **2026-04-24 (Assist dialog MD: GPT vs UI labels):** `phrygian_app.py` (`_assist_dialog_md_heading`, `role: gpt`), `assets/polyphonia_ui.js`, `build_index.py` / `index.html`, `docs/dev-notes/openai-assist-bridge.md`, `tests/test_phrygian_dialog_md.py`, `docs/repo-index.md`, `repo-index.yaml` (`polyphonia_sessions/dialogs/`).
- **2026-04-24 (Assist gpt_error role):** `phrygian_app.py` (`_assist_dialog_md_heading` для `gpt_error`), `assets/polyphonia_ui.js` (ошибки `openai_chat`), `build_index.py` / `index.html` (`.assist_msg_gpt_error`), `docs/dev-notes/openai-assist-bridge.md`, `docs/repo-index.md`, `tests/test_phrygian_dialog_md.py`, `repo-index.yaml`, `tasks/qa-change-gate.md`, `tasks/riff-apply-follow-up.md`.
- **2026-04-24 (UI режим offline/assist в настройках):** `phrygian_app.py` (`set_poly_mode`), `assets/polyphonia_ui.js`, `build_index.py` / `index.html`, `docs/dev-notes/openai-assist-bridge.md`, `docs/dev-workflow/commands-reference.md`, `tests/test_phrygian_set_poly_mode.py`, e2e `test_settings_poly_mode_switch`, `repo-index.yaml`, `tasks/qa-change-gate.md`.
- **2026-04-24 (Лаунчеры после build_index):** `build_index.py` пишет `run_polyphonia.bat`, `run_polyphonia.ps1`; на Windows создаёт ярлык рабочего стола `Polyphonia.lnk`; обновлены `README.md`, `repo-index.yaml`, `tasks/qa-change-gate.md`, `docs/repo-index.md`, `docs/dev-workflow/commands-reference.md`.
- **2026-04-24 (Стартовое окно ONLINE/OFFLINE + иконка):** `phrygian_app.py` (`launch_main`, `set_claude_api_key`, `get_claude_connection`, splash), `assets/polyphonia_startup.html`, `assets/polyphonia_launcher_icon.png`, `assets/polyphonia_app_icon.ico`, `build_index.py` (`try_write_polyphonia_ico`, ярлык с иконкой), `requirements-dev.txt` (Pillow), `docs/dev-notes/openai-assist-bridge.md`, `tests/test_phrygian_launch_main.py`, `repo-index.yaml`, `tasks/qa-change-gate.md`.
- **2026-04-24 (Окна + фикс сплэша + больше тестов):** `phrygian_app.py` (отдельное окно Assist/GPT, тайлинг 50/50, запуск Claude терминала отдельным окном), `assets/polyphonia_ui.js`, `build_index.py` (кнопки в настройках + режим `poly_view=assist`), `assets/polyphonia_startup.html` (OFFLINE запускает сразу, «Далее» работает по умолчанию в OFFLINE), `tests/test_phrygian_window_management.py`, обновлены `docs/dev-notes/openai-assist-bridge.md`, `docs/dev-notes/assist-llm-login-ux.md`.
- **2026-04-24 (Полное покрытие UX/AI: тест-кейсы + e2e сплэш/чат + сборка):** добавлен QA‑пакет `qa/packages/polyphonia-ux-ai-framework/` (test-cases), расширены unit тесты `tests/test_phrygian_launch_main.py`, `tests/test_phrygian_openai_chat_errors.py`, добавлены e2e `tests/e2e/test_startup_splash.py` и новые сценарии Assist, добавлен build‑тест `tests/test_build_pyinstaller_and_exe_smoke.py` (PyInstaller build, exe smoke по флагу), обновлены `repo-index.yaml`, `docs/dev-workflow/commands-reference.md`, `docs/dev-notes/openai-assist-bridge.md`.
- **2026-04-23 (Polyphonia modernization slice):** `build_index.py` (сетка «боксы», assist-панель, струны, аппликатура-эвристика, MusicXML), `assets/polyphonia_ui.js`, `phrygian_app.py` (`js_api` fullscreen), `riff_contract/`, `docs/schemas/riff-fragment-v0.schema.json`, `qa/examples/riff-fragment-v0.example.json`, `tasks/assist-variant-decision.md`, `docs/dev-notes/ai-framework-reaper-spike.md`, unit `tests/test_riff_contract.py`, e2e `tests/e2e/offline_scales/test_polyphonia_assist.py`, `requirements-dev.txt` (`jsonschema`), `pytest.ini` (`pythonpath`), `docs/architecture.md`, `docs/repo-index.md`, `docs/testing/offline-scales-chords-e2e.md`, `repo-index.yaml`, `impact-map.yaml`, `tasks/polyphonia-modernization-roadmap.md`.
- Проверка: `python scripts/check_change_gate.py --staged` после `git add` ожидаемых файлов; перед пушем — `python scripts/check_change_gate.py` (после `git fetch`); при отсутствии `origin/develop` — задать `PETS_CHANGE_GATE_BASE` или `--base`.

## Steps

- [x] Канонический док и скрипт
- [x] Агент, команда, правило Cursor
- [x] Записи в `repo-index.yaml` и задача в `tasks/`

## Review Notes

- Синхронизация `.claude/` — `python scripts/sync_configs.py` после правок `.cursor/`.
