# Offline scales / chords — automated E2E checks

## Confirmed

- Автотесты в `tests/e2e/` открывают собранный `index.html` по `file://` из корня репозитория и проверяют DOM и классы подсветки через Playwright.
- Перед каждым тестовым сеансом вызывается `python build_index.py` (см. `tests/e2e/conftest.py`).
- Планы, кейсы, трассировка и runbook: `qa/packages/offline-scales-fretboard/`.
- Машинные отчёты (JUnit и т.п.) — только в `qa/results/` (каталог в `.gitignore`, в git не попадает).

## Как запустить

```powershell
Set-Location D:\Reps\PETS
pip install -r requirements-dev.txt
playwright install chromium
python -m pytest tests/e2e/test_offline_scales_chords_e2e.py -v
```

С JUnit в игнорируемый каталог:

```powershell
New-Item -ItemType Directory -Force -Path qa/results | Out-Null
python -m pytest tests/e2e/test_offline_scales_chords_e2e.py -v --junitxml=qa/results/junit.xml
```

## Risk

- Headless Chromium может отличаться от WebView2 в `pywebview` по визуальным деталям; проверяются DOM и классы.

## Deferred

- Автоматическая проверка отсутствия сетевых запросов при `file://`.
