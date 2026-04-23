# Title

Fix stringed fretboard rendering in generated app UI

## Objective

Restore the DOM structure expected by the existing stringed-instrument CSS so the fretboard renders correctly in the desktop app.

## Confirmed

- The app opens through `phrygian_app.py` and loads the generated `index.html`.
- Current `assets/*.css` for stringed instruments expect elements like `#fret_wood`, `#frets_con`, `.string`, and a spacer node in `#fret_note_con`.
- The generated fretboard markup had dropped those nodes, causing broken layout.
- The offline page does not provide the full site metadata shell, so `PageMeta` behavior must be neutralized for local runtime.
- The generated offline page must explicitly trigger initial scale rendering after `ScalesPage.init()`.
- The legacy minified scale-page logic is not reliable in the offline shell, so the generated page now needs an explicit offline renderer for scale info, fretboard highlighting, and chord-table interactions.

## Assumption

- Restoring the previous structural wrappers is sufficient to recover the intended layout without changing the data model or interaction flow.

## Risk

- Any remaining mismatch between generated markup and legacy JS/CSS may still affect non-guitar stringed instruments.

## Deferred

- Refactoring fretboard generation into a clearer authored template.

## Open Question

- Whether the long-term source of truth for this UI should stay in `build_index.py` string assembly or move to a dedicated template.

## Source Of Truth

- `build_index.py`
- `assets/instrument_stringed.min.css`
- instrument-specific CSS files under `assets/`

## Steps

- [x] Compare generated fretboard markup with the CSS-expected structure.
- [x] Restore missing structural nodes in `build_index.py`.
- [x] Restore offline-safe initialization and initial scale rendering.
- [x] Replace fragile offline scale/chord rendering with explicit generated-page logic.
- [x] Rebuild `index.html` and verify the generated markup.

## Review Notes

- Fix stays inside the current generated-page runtime and does not change musical data files.

## Automated verification

- E2E (Playwright + pytest): `tests/e2e/offline_scales/` (маркер `e2e`).
- QA-пакет (кейсы, трассировка, runbook): `qa/packages/offline-scales-fretboard/`.
- Локальные отчёты: `qa/results/` (в `.gitignore`).
- Краткая инструкция: `docs/testing/offline-scales-chords-e2e.md`.
