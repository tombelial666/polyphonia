# Traceability matrix — offline scales / fretboard / chords

| TC ID | Кратко | Автотест (pytest) | Evidence (локально) |
|-------|--------|-------------------|------------------------|
| TC-PETS-SCALE-01 | A Major, тексты + root | `test_default_a_major_scale_info_and_root_highlight` | `qa/results/junit.xml` после прогона |
| TC-PETS-SCALE-02 | A natural minor | `test_natural_minor_changes_scale_notes` | `qa/results/junit.xml` |
| TC-PETS-CHORD-01 | Клик аккорда | `test_chord_click_shows_chord_info_and_highlight` | `qa/results/junit.xml` |
| TC-PETS-UX-01 | Капо | `test_capo_moves_capo_marker_and_keeps_scale_highlight` | `qa/results/junit.xml` |
| TC-PETS-UX-02 | Minor third + melodic minor | `test_alternate_tuning_minor_third_still_renders_scale` | `qa/results/junit.xml` |
| TC-PETS-UX-03 | Левша | `test_lefty_toggles_display_class` | `qa/results/junit.xml` |
| TC-PETS-UX-04 | Бемоли | `test_flat_accidental_updates_note_labels` | `qa/results/junit.xml` |
| TC-PETS-MANUAL-NET-01 | Нет внешней сети | *ручная* | n/a |

## Источники истины

- Логика рендера: `build_index.py` → `index.html`.
- Данные гамм: `assets/scales.data.min.js`.
- Данные аккордов: `assets/chords.data.min.js`.
- Строи: `assets/all_instruments.js`.
