# Test execution runbook — offline scales / fretboard / chords

## Confirmed

- Корень репозитория PETS — рабочий каталог для всех команд ниже.
- JUnit и прочие машинные отчёты пишутся **только** в `qa/results/` (не коммитятся).

## Предусловия

1. Python 3.11+.
2. Зависимости:

```powershell
pip install -r requirements-dev.txt
```

3. Chromium для Playwright (однократно при ошибке):

```powershell
playwright install chromium
```

## Прогон с JUnit

```powershell
Set-Location <корень-PETS>
New-Item -ItemType Directory -Force -Path qa/results | Out-Null
python -m pytest tests/e2e/test_offline_scales_chords_e2e.py -v `
  --junitxml=qa/results/junit.xml
```

## Ожидаемый результат

- Консоль: `7 passed`.
- Файл: `qa/results/junit.xml` с `tests="7"` и `failures="0"` (файл остаётся только у вас локально или в артефактах CI).

## После прогона

1. При необходимости обновить дату и метрики в `test-execution-summary.md`.
2. Опционально: сохранить фрагмент консоли в `qa/results/console.txt` (тоже не коммитить).

## Ручной смоук приложения

```powershell
Set-Location <корень-PETS>
python build_index.py
python phrygian_app.py
```
