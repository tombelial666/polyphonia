# Offline scales / chords — automated E2E checks

## Confirmed

- Автотесты в `tests/e2e/offline_scales/` открывают собранный `index.html` по `file://` из корня репозитория и проверяют DOM и классы подсветки через Playwright (маркер `e2e`).
- Дополнительный smoke: `test_polyphonia_assist.py` — панель Assist, `window.polyphonia`, пресет раскладки Wide, скрытие струны через `poly_hide_s*`.
- Перед каждым тестовым сеансом вызывается `python build_index.py` (см. `tests/e2e/conftest.py`).
- Планы, кейсы, трассировка и runbook: `qa/packages/offline-scales-fretboard/`.
- Машинные отчёты (JUnit и т.п.) — только в `qa/results/` (каталог в `.gitignore`, в git не попадает).

## Как запустить

```powershell
Set-Location D:\Reps\PETS
pip install -r requirements-dev.txt
playwright install chromium
python -m pytest tests/e2e/offline_scales -v -m e2e
```

С JUnit в игнорируемый каталог:

```powershell
New-Item -ItemType Directory -Force -Path qa/results | Out-Null
python -m pytest tests/e2e/offline_scales -v -m e2e --junitxml=qa/results/junit.xml
```

## Risk

- Headless Chromium может отличаться от WebView2 в `pywebview` по визуальным деталям; проверяются DOM и классы.

## Confirmed (CI)

- Прогон того же набора сценариев в GitHub Actions: `.github/workflows/ci.yml` (job `e2e` после `change-gate`).

## Deferred

- Автоматическая проверка отсутствия сетевых запросов при `file://`.
