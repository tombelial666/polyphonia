# AI review — test design: offline scales / fretboard / chords

## Confirmed

- Фича: офлайн-страница `index.html` (сборка `build_index.py`), оболочка `phrygian_app.py`, данные в `assets/*.js` / `assets/*.css`.
- Критичный путь: выбор ноты и гаммы → заполнение `Scale Info` → подсветка `.in_scale` / `.scale_root` на грифе → таблица аккордов → клик по аккорду → `Chord Info` и `.in_chord` на грифе.
- Автоматизация **validation-backed**: Playwright открывает собранный `index.html` по `file://` и проверяет DOM и классы.

## Assumption

- Поведение в Chromium headless эквивалентно ручному просмотру в `pywebview` для проверяемых селекторов.

## Risk

- Расхождение `file://` и WebView2 в `pywebview` на редких визуальных кейсах не покрывается этими тестами.

## Deferred

- Полная матрица всех инструментов и всех строев из `all_instruments.js`.

## Покрытие уровней

| Уровень | Что проверяем | Инструмент |
|---------|----------------|------------|
| L1 | Сборка `index.html` без ошибки | `build_index.py` в `tests/e2e/conftest.py` |
| L2 | Текст блока гаммы | Playwright `expect` по `#info_scale_*` |
| L3 | Подсветка на грифе | Классы на `#f_0 .s_*` |
| L4 | Таблица аккордов и клик | Первая активная кнопка в первой строке |
| L5 | Капо и левша | `#capo_con` родитель, класс `is_lefty` |
| L6 | Нестандартный строй | `minor-third` + `melodic-minor` |

## Негативные сценарии (ручные / следующий спринт)

- Отсутствие внешних сетевых запросов: DevTools или Playwright `page.on("request")`.
