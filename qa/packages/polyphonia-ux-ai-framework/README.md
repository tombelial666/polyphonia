# QA package: Polyphonia UX + AI framework

## Purpose

Свести в одном месте проверяемые требования и тест‑кейсы для:

- стартового окна (ONLINE/OFFLINE) и переходов режима;
- Assist чата (Draft/GPT), настроек, логов;
- pywebview bridge (Python API), ключей и сетевых ошибок;
- оконных функций Windows (detatch/tile) и запуска Claude терминала;
- сборки PyInstaller (`polyphonia.spec`) и запуска `dist/polyphonia.exe`;
- AI framework артефактов (`riff_contract/`, schema/example).

## Canonical pointers

- Runtime: `phrygian_app.py`, `build_index.py`, `index.html`, `assets/`
- Tests: `tests/` (unit), `tests/e2e/` (Playwright)
- Change gate: `docs/dev-workflow/qa-change-gate.md`, `scripts/check_change_gate.py`

## Files in this package

- `test-cases.md`: полный набор тест‑кейсов (unit/e2e/build/manual) с моками внешних сервисов.

