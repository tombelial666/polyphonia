# Spike: `C:\ai-framework-reaper` (reuse vs PETS)

## Confirmed

- Каталог на машине разработчика существует и содержит Python-пакет `reaper-ai-framework` (`pyproject.toml`), `README.md`, `docs/`, `src/`, `tests/`, `examples/`, `fixtures/`.
- Позиционирование фреймворка: **tab-first**, canonical score model, **REAPER-first MIDI-oriented scaffolds**, **human-in-the-loop**, MusicXML как **технический мост** (см. README репозитория).
- Опциональная зависимость **`PyGuitarPro`** помечена как dev/guitarpro slice, не ядро MVP — совпадает с планом PETS: нативный `.gp` — фаза 2 после spike.

## Assumption

- CI и чужие машины **не** имеют этого пути; интеграция в PETS не должна требовать его наличия.

## Risk

- Внешний путь **не** является git source-of-truth для PETS; submodule или копирование целого дерева — отдельное решение владельца.

## Reuse (кандидаты)

| Область | Комментарий |
|--------|-------------|
| Документированные паттерны pipeline «structured source → canonical model → export» | Полезно для **фазы 2** экспорта GP / MusicXML bridge в PETS без прямой зависимости. |
| Идея **MusicXML как мост**, не «лицо продукта» | Уже совпадает с MVP PETS (MusicXML snapshot из UI). |
| Опциональный **PyGuitarPro** | При spike нативного GP — оценить лицензию/объём; не тянуть в runtime PyInstaller до явного решения. |

## Reject / не тянуть в PETS сейчас

| Область | Комментарий |
|--------|-------------|
| Полный REAPER-oriented pipeline, Nu-metal fixtures, vision path | Вне scope текущего `pywebview` + offline Polyphonia; противоречит минимальному runtime. |
| Замена **детерминированных** `assets/` данными из фреймворка | Риск расхождения с грифом; MANIFEST требует разделения истин. |

## Open Question

- Submodule vs «только доки + выборочный код» — решение после отдельной задачи на лицензии и размер бинарника (`polyphonia.spec`).
