# Legacy Assets Index

## Purpose

This file is the detailed index of `assets/`. It explains the role of every asset file family and highlights source-of-truth risks inside the current legacy frontend.

## Asset Layer Summary

`assets/` is a flat legacy frontend bundle. It contains:

- instrument registries
- per-instrument data snapshots
- theory data
- page logic
- DOM/UI support classes
- CSS bundles
- a piano HTML fragment
- vendor JavaScript

## Category Map

| Category | Files | Meaning |
|---|---|---|
| Instrument registry | `all_instruments.js` | Multi-instrument source registry |
| Instrument snapshots | `instrument.*.data.min.js` | Per-instrument `instrumentInfo` bundles |
| Theory data | `chords.data.min.js`, `scales.data.min.js` | Chord and scale dictionaries |
| UI/domain logic | `*.class.min.js`, `scalesPage.min.js` | Singleton-style page and DOM logic |
| Vendor | `jquery.min.js` | Third-party dependency |
| Styling | `*.min.css` | Base and instrument-specific styling |
| HTML fragment | `_piano_html.txt` | Inserted piano markup used during HTML assembly |
| Media | `chords-logo.png` | Logo used by the UI |

## Instrument Registry

| Path | Status | Description | Notes |
|---|---|---|---|
| `assets/all_instruments.js` | authoritative registry | Defines `allInstrumentsData` for all instrument families with `notes`, fret limits, tunings, and `start_octave_num` | One of the few readable non-minified files in `assets`; high-value source file |

## Instrument Snapshot Files

These files each define a single global `instrumentInfo` object for one instrument page context.

| Path | Instrument | Status | Description |
|---|---|---|---|
| `assets/instrument.guitar.data.min.js` | guitar | duplicated data source | Snapshot for 6-string guitar |
| `assets/instrument.bass-guitar.data.min.js` | bass guitar | duplicated data source | Snapshot for bass guitar |
| `assets/instrument.ukulele.data.min.js` | ukulele | duplicated data source | Snapshot for ukulele |
| `assets/instrument.violin-fiddle.data.min.js` | violin / fiddle | duplicated data source | Snapshot for violin/fiddle |
| `assets/instrument.mandolin.data.min.js` | mandolin | duplicated data source | Snapshot for mandolin |
| `assets/instrument.piano.data.min.js` | piano | duplicated data source | Snapshot for piano |
| `assets/instrument.5-string-bass-guitar.data.min.js` | 5-string bass | duplicated data source | Snapshot for 5-string bass |
| `assets/instrument.6-string-bass-guitar.data.min.js` | 6-string bass | duplicated data source | Snapshot for 6-string bass |
| `assets/instrument.7-string-guitar.data.min.js` | 7-string guitar | duplicated data source | Snapshot for 7-string guitar; includes the added `Drop G` tuning |
| `assets/instrument.8-string-guitar.data.min.js` | 8-string guitar | duplicated data source | Snapshot for 8-string guitar |
| `assets/instrument.9-string-guitar.data.min.js` | 9-string guitar | duplicated data source | Snapshot for 9-string guitar |
| `assets/instrument.10-string-guitar.data.min.js` | 10-string guitar | duplicated data source | Snapshot for 10-string guitar |
| `assets/instrument.baritone-guitar.data.min.js` | baritone guitar | duplicated data source | Snapshot for baritone guitar |
| `assets/instrument.5-string-violin-fiddle.data.min.js` | 5-string violin/fiddle | duplicated data source | Snapshot for 5-string violin/fiddle |

### Instrument Snapshot Risk

The per-instrument files duplicate information already present in `all_instruments.js`. This is a real maintenance risk:

- registry updated, snapshot stale
- snapshot updated, registry stale
- agents unsure which file is authoritative for a tuning change

For now:

- `all_instruments.js` should be treated as the primary readable registry
- `instrument.*.data.min.js` files are required runtime companions and must stay aligned

## Theory Data Files

| Path | Status | Description | Notes |
|---|---|---|---|
| `assets/chords.data.min.js` | runtime data source | Defines `allChordAr`, the chord dictionary used by page logic | Legacy minified data bundle |
| `assets/scales.data.min.js` | runtime data source | Defines `allScaleAr`, the scale dictionary used by page logic | Legacy minified data bundle; duplicate or repeated scale code patterns were observed and should be treated carefully |

## Logic Files

| Path | Status | Description | Main Dependency Role |
|---|---|---|---|
| `assets/jquery.min.js` | vendor dependency | jQuery runtime used by the page logic | DOM selection and event binding |
| `assets/note.class.min.js` | runtime logic | Normalizes note naming, note keys, sharps/flats, display formatting | Base helper for scale and chord logic |
| `assets/scale.class.min.js` | runtime logic | Holds selected scale state and loads scale-note arrays from `allScaleAr` | Depends on `note.class.min.js` and `scales.data.min.js` |
| `assets/chord.class.min.js` | runtime logic | Holds selected chord state and loads chord-note arrays from `allChordAr` | Depends on `note.class.min.js` and `chords.data.min.js` |
| `assets/instrumentOptions.class.min.js` | runtime logic | Handles tuning selection, custom tuning, lefty mode, capo, fretboard display updates | Critical bridge between data and visible UI |
| `assets/scalesStringed.class.min.js` | runtime logic | Applies scale/chord highlighting to the fretboard | Depends on `InstrumentOptions`, `Scale`, and `Chord` |
| `assets/keyPositionPiano.class.min.js` | runtime logic | Controls piano key highlighting and display state | Depends on piano fragment markup and page state |
| `assets/pageMeta.class.min.js` | runtime logic | Handles page metadata, navigation state, canonical links, and history logic | Carries assumptions from the original website context |
| `assets/scalesPage.min.js` | runtime page controller | Initializes scale page behavior, binds forms, fills chord tables, coordinates updates | Main page orchestration file for scales mode |

## CSS Files

### Base And Shared CSS

| Path | Status | Description |
|---|---|---|
| `assets/styles.min.css` | runtime styling | Base site-level CSS |
| `assets/scales_info.min.css` | runtime styling | Scale/chord information panel styles |
| `assets/instrument_options.min.css` | runtime styling | Form options and tuning-control styles |
| `assets/instrument_stringed.min.css` | runtime styling | Shared stringed-instrument fretboard styles |

### Instrument-Specific CSS

| Path | Instrument |
|---|---|
| `assets/instrument_guitar.min.css` | guitar |
| `assets/instrument_bass-guitar.min.css` | bass guitar |
| `assets/instrument_ukulele.min.css` | ukulele |
| `assets/instrument_violin-fiddle.min.css` | violin / fiddle |
| `assets/instrument_mandolin.min.css` | mandolin |
| `assets/instrument_piano.min.css` | piano |
| `assets/instrument_5-string-bass-guitar.min.css` | 5-string bass |
| `assets/instrument_6-string-bass-guitar.min.css` | 6-string bass |
| `assets/instrument_7-string-guitar.min.css` | 7-string guitar |
| `assets/instrument_8-string-guitar.min.css` | 8-string guitar |
| `assets/instrument_9-string-guitar.min.css` | 9-string guitar |
| `assets/instrument_10-string-guitar.min.css` | 10-string guitar |
| `assets/instrument_baritone-guitar.min.css` | baritone guitar |
| `assets/instrument_5-string-violin-fiddle.min.css` | 5-string violin/fiddle |

These CSS bundles are runtime assets, but they are minified and therefore not ideal authoring sources.

## HTML Fragment And Media

| Path | Status | Description |
|---|---|---|
| `assets/_piano_html.txt` | build input | Static HTML fragment for the piano section inserted into the generated page |
| `assets/chords-logo.png` | runtime media | Logo referenced by the current UI |

## Current Dependency Shape

```text
all_instruments.js
  -> runtime selection metadata
  -> overlaps with instrument.*.data.min.js

instrument.*.data.min.js
  -> instrumentOptions.class.min.js
  -> scalesPage.min.js

scales.data.min.js + chords.data.min.js
  -> scale.class.min.js / chord.class.min.js
  -> scalesPage.min.js

note.class.min.js
  -> scale.class.min.js
  -> chord.class.min.js
  -> instrumentOptions.class.min.js
  -> scalesPage.min.js

scalesPage.min.js
  -> instrumentOptions.class.min.js
  -> scalesStringed.class.min.js
  -> keyPositionPiano.class.min.js
  -> pageMeta.class.min.js
```

## Source-Of-Truth Assessment

### Confirmed

- `all_instruments.js` is the clearest readable source for instrument configuration intent.
- `instrument.*.data.min.js` files are required runtime payloads and currently function as duplicated snapshots.
- Theory and UI logic are mostly minified bundles without visible unminified source files in this repository.

### Risk

- Direct edits to minified files are error-prone.
- Duplicate instrument data raises drift risk.
- Repeated or overlapping scale identifiers inside `scales.data.min.js` may create hidden behavior traps.

### Open Question

- Should future refactoring move these minified data and logic bundles into cleaner authored source modules before any desktop-shell migration begins?
