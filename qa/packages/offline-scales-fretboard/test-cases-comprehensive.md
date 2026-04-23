# Test cases — offline scales / fretboard / chords

## Summary

- **Total automated cases**: 7 (pytest + Playwright, каталог `tests/e2e/offline_scales/`, маркер `e2e`)
- **Total documented manual follow-ups**: 1 (сеть)
- **Primary risk**: расхождение данных `assets/scales.data.min.js` и ожидаемой теории; автотесты фиксируют поведение текущих данных + UI.

---

### TC-PETS-SCALE-01 — A Major: тексты и root на грифе

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-SCALE-01 |
| **Priority** | P1 |
| **Type** | E2E / DOM |

**Preconditions:** выполнен `python build_index.py`, открыт `index.html`, инструмент Guitar.

**Steps:**

1. Выбрать ноту `A`, гамму `Major`.
2. Прочитать `#info_scale_name`, `#info_scale_notes`.
3. Проверить классы у `#f_0 .s_1` и `#f_0 .s_5`.

**Expected:**

- В названии есть `A` и `Major`.
- В списке нот есть A, B, D, E; диезы отображаются символом U+266F.
- `.s_1` на нулевом ладу имеет `in_scale` и `scale_root` (ля на 5-й струне).
- `.s_5` на нулевом ладу имеет `in_scale` (ми басовой).

**Automation:** `test_a_major_scale_info_and_root_highlight` (`test_a_major_scale_info.py`)

---

### TC-PETS-SCALE-02 — A Natural Minor: смена набора нот

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-SCALE-02 |
| **Priority** | P1 |
| **Type** | E2E / регрессия данных |

**Steps:** выбрать `A` + `natural-minor`, прочитать `#info_scale_notes`.

**Expected:** в тексте присутствуют ноты, характерные для лада (проверка якорей `C` и `F` в тесте как отличие от мажора).

**Automation:** `test_natural_minor_changes_scale_notes`

---

### TC-PETS-CHORD-01 — клик по аккорду из таблицы

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-CHORD-01 |
| **Priority** | P1 |
| **Type** | E2E / UI |

**Steps:**

1. `A` + `Major`.
2. Клик по первой **не** disabled кнопке в первой строке таблицы (`#scale_chord_table tbody tr:first-child`).

**Expected:**

- `#chord_info` без класса `hidden`.
- `#info_chord_notes` не пустой.
- На грифе `#f_0 .s_1` получает класс `in_chord`.

**Automation:** `test_chord_click_shows_chord_info_and_highlight`

---

### TC-PETS-UX-01 — каподастр

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-UX-01 |
| **Priority** | P2 |
| **Type** | E2E |

**Steps:** `A` + `Major`, `Capo` = лад `2`.

**Expected:** `#stringed_display` с классом `has_capo`; `#capo_con` вложен в `#f_2`.

**Automation:** `test_capo_moves_capo_marker_and_keeps_scale_highlight`

---

### TC-PETS-UX-02 — альтернативный строй Minor Third + Melodic Minor

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-UX-02 |
| **Priority** | P2 |
| **Type** | E2E / регрессия кастомного строя |

**Steps:** tuning `minor-third`, нота `A`, гамма `melodic-minor`.

**Expected:** непустой `#info_scale_notes`, заголовок содержит `Melodic Minor`, есть хотя бы одна `.in_scale` ячейка.

**Automation:** `test_alternate_tuning_minor_third_still_renders_scale`

---

### TC-PETS-UX-03 — левша

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-UX-03 |
| **Priority** | P3 |
| **Type** | E2E |

**Steps:** включить `Left Handed`, затем выключить.

**Expected:** класс `is_lefty` на `#stringed_display` переключается.

**Automation:** `test_lefty_toggles_display_class`

---

### TC-PETS-UX-04 — бемоли в accidental

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-UX-04 |
| **Priority** | P2 |
| **Type** | E2E |

**Steps:** `Accidental` = `Flat`, `A` + `Major`.

**Expected:** в `#info_scale_notes` присутствует символ бемоля U+266D.

**Automation:** `test_flat_accidental_updates_note_labels`

---

### TC-PETS-MANUAL-NET-01 — отсутствие сетевых запросов

| Field | Value |
|-------|-------|
| **ID** | TC-PETS-MANUAL-NET-01 |
| **Priority** | P2 |
| **Type** | Ручная / наблюдаемость |

**Steps:** открыть DevTools, вкладка Network, перезагрузить страницу, пощёлкать по UI.

**Expected:** нет запросов к внешним хостам (кроме `about:blank` / внутренних схем браузера).

**Automation:** Deferred (можно добавить listener в `tests/e2e/`).
