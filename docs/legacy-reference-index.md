# Legacy Reference Index

## Purpose

This file maps the non-core legacy layers that sit beside the active PETS runtime: build caches, packaging leftovers, saved-page artifacts, and duplicate reference bundles.

## Layer Summary

| Path | Category | Status | Description |
|---|---|---|---|
| `build/` | packaging cache | generated, disposable | PyInstaller analysis output and warnings |
| `dist/` | packaging output | generated, disposable | Expected packaged executables or output bundles; currently ignored |
| `A Phrygian Dominant.html` | saved-page reference | reference | Saved website page, not the current app entry |
| `A Phrygian Dominant.spec` | legacy packaging spec | reference | Old PyInstaller spec oriented around the saved-page path |
| `A Phrygian Dominant_files/` | saved-page resource bundle | reference, partially disposable | Resource bundle captured by browser save-page behavior; includes duplicates and unrelated web widgets |

## Build Layer

### `build/polyphonia/`

| Path | Status | Description |
|---|---|---|
| `build/polyphonia/Analysis-00.toc` | generated | PyInstaller analysis table for `polyphonia.spec` |
| `build/polyphonia/EXE-00.toc` | generated | PyInstaller executable table |
| `build/polyphonia/PKG-00.toc` | generated | PyInstaller package table |
| `build/polyphonia/PYZ-00.toc` | generated | PyInstaller Python archive table |
| `build/polyphonia/warn-polyphonia.txt` | generated diagnostic | Packaging warnings for the active packaging path |
| `build/polyphonia/xref-polyphonia.html` | generated diagnostic | Cross-reference report created by PyInstaller |

### `build/ChordRocks/` (legacy cache)

If this directory still exists locally, it came from older PyInstaller runs when the spec file was named `ChordRocks.spec`. It is not part of the current authoritative packaging path and can be deleted.

### `build/A Phrygian Dominant/`

| Path | Status | Description |
|---|---|---|
| `build/A Phrygian Dominant/Analysis-00.toc` | generated legacy | PyInstaller analysis output from an older packaging scenario |
| `build/A Phrygian Dominant/EXE-00.toc` | generated legacy | Old executable table |
| `build/A Phrygian Dominant/PKG-00.toc` | generated legacy | Old package table |
| `build/A Phrygian Dominant/PYZ-00.toc` | generated legacy | Old Python archive table |
| `build/A Phrygian Dominant/warn-A Phrygian Dominant.txt` | generated diagnostic legacy | Packaging warnings for the legacy spec |
| `build/A Phrygian Dominant/xref-A Phrygian Dominant.html` | generated diagnostic legacy | Cross-reference report for the legacy spec |

### Build-Layer Interpretation

- `build/polyphonia/` belongs to the active packaging path (`polyphonia.spec`).
- `build/A Phrygian Dominant/` belongs to an older or alternative packaging attempt.
- none of these files are authoritative source files.

## Dist Layer

| Path | Status | Description |
|---|---|---|
| `dist/` | generated, disposable | Expected PyInstaller output directory; ignored in git and not part of project truth |

## Saved-Page Artifacts

### Root Saved-Page Files

| Path | Status | Description |
|---|---|---|
| `A Phrygian Dominant.html` | reference | Browser-saved Chord.Rocks page snapshot |
| `A Phrygian Dominant.spec` | reference | Legacy PyInstaller spec built around the saved-page artifact |

### `A Phrygian Dominant.html`

This file is a saved webpage, not the current PETS runtime entry. It can easily mislead agents because:

- it looks like a complete HTML application
- it references a local `_files/` folder full of JS and CSS
- it resembles the same product domain as the real PETS app

But the active shell loads `index.html`, not this file.

### `A Phrygian Dominant.spec`

This spec is legacy and potentially misleading:

- it packages `A Phrygian Dominant.html` and `A Phrygian Dominant_files/`
- the current shell in `phrygian_app.py` still opens `index.html`

So this spec is not aligned with the current runtime path and must be treated as historical reference only.

## `A Phrygian Dominant_files/` Inventory

### Direct Duplicates Of Active Runtime Assets

These files duplicate current `assets/`-layer files and should not be used as editing targets:

- `A Phrygian Dominant_files/chords.data.min.js`
- `A Phrygian Dominant_files/scales.data.min.js`
- `A Phrygian Dominant_files/jquery.min.js`
- `A Phrygian Dominant_files/keyPositionPiano.class.min.js`
- `A Phrygian Dominant_files/pageMeta.class.min.js`
- `A Phrygian Dominant_files/chord.class.min.js`
- `A Phrygian Dominant_files/scale.class.min.js`
- `A Phrygian Dominant_files/note.class.min.js`
- `A Phrygian Dominant_files/instrumentOptions.class.min.js`
- `A Phrygian Dominant_files/scalesStringed.class.min.js`
- `A Phrygian Dominant_files/scalesPage.min.js`
- instrument CSS and data files corresponding to the same names present under `assets/`

### Duplicate-Snapshot Files With `Без названия`

These are browser-save or duplicate leftovers and are not part of the real project:

- `A Phrygian Dominant_files/socialMedia.min.js.Без названия`
- `A Phrygian Dominant_files/scalesStringed.class.min.js.Без названия`
- `A Phrygian Dominant_files/scalesPage.min.js.Без названия`
- `A Phrygian Dominant_files/scale.class.min.js.Без названия`
- `A Phrygian Dominant_files/chord.class.min.js.Без названия`
- `A Phrygian Dominant_files/scales.data.min.js.Без названия`
- `A Phrygian Dominant_files/chords.data.min.js.Без названия`
- `A Phrygian Dominant_files/note.class.min.js.Без названия`
- `A Phrygian Dominant_files/pageMeta.class.min.js.Без названия`
- `A Phrygian Dominant_files/instrumentOptions.class.min.js.Без названия`
- `A Phrygian Dominant_files/instrument.7-string-guitar.data.min.js.Без названия`
- `A Phrygian Dominant_files/jquery.min.js.Без названия`
- `A Phrygian Dominant_files/button.856debeac157d9669cf51e73a08fbc93.js.Без названия`
- `A Phrygian Dominant_files/sdk.js.Без названия`
- `A Phrygian Dominant_files/widgets.js.Без названия`
- `A Phrygian Dominant_files/analytics.js.Без названия`

### Social / Widget / Browser-Save Noise

These are not part of the PETS runtime logic:

- `A Phrygian Dominant_files/widget_iframe.2f70fb173b9000da126c79afe2098f02.html`
- `A Phrygian Dominant_files/like.html`
- `A Phrygian Dominant_files/tweet_button.2f70fb173b9000da126c79afe2098f02.en.html`
- `A Phrygian Dominant_files/saved_resource.html`
- `A Phrygian Dominant_files/saved_resource`
- `A Phrygian Dominant_files/js`
- `A Phrygian Dominant_files/js(1)`
- `A Phrygian Dominant_files/ARUN3D9gcNG.css`

### Instrument-CSS And Data Duplicates

The following families exist inside `A Phrygian Dominant_files/` and duplicate active runtime families from `assets/`:

- `instrument_*.min.css`
- `instrument.*.data.min.js`
- `styles.min.css`
- `instrument_stringed.min.css`
- `instrument_options.min.css`
- `scales_info.min.css`

## Agent Confusion Traps

### Confirmed

- `A Phrygian Dominant.html` looks like a full runnable app even though it is not the current entry point.
- `A Phrygian Dominant_files/` contains many files whose names match active `assets/` files.
- `A Phrygian Dominant.spec` resembles a valid packaging path but is not aligned with the active runtime.
- `build/A Phrygian Dominant/` visually reinforces the false idea that the saved-page path is still an active product path.

### Risk

- Agents may edit duplicate JS/CSS in `A Phrygian Dominant_files/` instead of the active `assets/` tree.
- Agents may read `warn-*.txt` or `xref-*.html` as product documentation rather than one-time packaging diagnostics.
- Legacy packaging and saved-page artifacts may be mistaken for product migration paths.

### Recommended Interpretation

- treat `build/` and `dist/` as disposable packaging layers
- treat `A Phrygian Dominant*` as reference-only legacy residue
- treat `assets/`, `build_index.py`, `index.html`, `phrygian_app.py`, and `polyphonia.spec` as the current runtime-relevant path
