# Test cases — Polyphonia UX + AI framework

## Convention

- **Type**: `unit` | `e2e` | `build` | `manual`
- **Mocks**: what must be stubbed (OpenAI HTTP, pywebview JS bridge, OS APIs)
- **Risk**: why it matters / what it prevents

---

## Startup splash (assets/polyphonia_startup.html)

### TC-SPLASH-001 — OFFLINE default launch
- **Type**: e2e
- **Preconditions**: open `assets/polyphonia_startup.html` in Playwright
- **Mocks**: `window.pywebview.api.launch_main` → records payload; returns `{"ok":true}`
- **Steps**:
  - load page
  - click `Далее`
- **Expected**:
  - `launch_main` called once
  - payload `mode="offline"`
- **Risk**: prevents regressions where UI blocks without selection

### TC-SPLASH-002 — ONLINE shows key panel and submits keys
- **Type**: e2e
- **Mocks**: `launch_main` stub returning ok
- **Steps**:
  - click `ONLINE`
  - fill OpenAI and Claude fields
  - click `Далее`
- **Expected**:
  - payload includes `mode="assist"`, both keys passed as strings
  - loading state shown while awaiting promise

### TC-SPLASH-003 — OFFLINE button launches immediately
- **Type**: e2e
- **Mocks**: `launch_main` stub
- **Steps**:
  - click `ONLINE` (panel opens)
  - click `OFFLINE`
- **Expected**:
  - `launch_main` called with `mode="offline"` without needing `Далее`
- **Risk**: prevents “returns back” UX bug

### TC-SPLASH-004 — launch_main error shown in UI
- **Type**: e2e
- **Mocks**: `launch_main` returns `{"ok":false,"message":"boom"}`
- **Steps**: click `Далее`
- **Expected**: error text rendered into `#err`, no navigation performed

---

## Poly mode + URL stability (file://)

### TC-MODE-001 — mode passed via hash works (index.html#poly_mode=assist)
- **Type**: unit (JS) + e2e
- **Mocks**: none for JS parsing; in e2e just open file URL with hash
- **Expected**: `getPolyMode()` returns `assist`
- **Risk**: prevents WebView2 `ERR_FILE_NOT_FOUND` due to query on file://

### TC-MODE-002 — assist view query coexists with hash
- **Type**: unit (JS)
- **Input**: `index.html?poly_view=assist#poly_mode=assist`
- **Expected**: `assist` mode (hash parsed before appended params)

---

## Assist Chat UX (ChatGPT-like)

### TC-ASSIST-001 — default send mode is Draft (no network)
- **Type**: e2e
- **Mocks**: `window.pywebview.api.openai_chat` spy; should not be called
- **Steps**:
  - open `index.html#poly_mode=assist`
  - open Assist
  - type message
  - click `Отправить`
- **Expected**:
  - message appended as `user`
  - system lines about draft/context appended
  - `openai_chat` not called

### TC-ASSIST-002 — GPT mode sends via openai_chat
- **Type**: e2e
- **Mocks**:
  - `openai_chat` returns `{"ok":true,"content":"hi"}`
  - `get_openai_connection` returns `{"ok":true,"ui_mode":"assist","source":"session"}`
- **Steps**:
  - set send mode `GPT`
  - type message
  - click send
- **Expected**:
  - `openai_chat` called with `include_context` reflecting checkbox
  - response appended with role `gpt`

### TC-ASSIST-003 — GPT disabled in offline mode
- **Type**: e2e
- **Mocks**: none
- **Steps**:
  - open `index.html#poly_mode=offline`
  - open Assist (if available)
  - set send mode GPT, send
- **Expected**: system message that GPT disabled / switch mode; no call

### TC-ASSIST-004 — GPT error formatting: insufficient_quota becomes short message
- **Type**: e2e + unit (JS formatter)
- **Mocks**: `openai_chat` returns `{"ok":false,"message":"{...json error...}"}` or raw json body
- **Expected**: rendered error line like `You exceeded your current quota (insufficient_quota)` not full JSON dump

### TC-ASSIST-005 — Ctrl+Enter sends
- **Type**: e2e
- **Mocks**: like TC-ASSIST-002
- **Steps**: type and press `Ctrl+Enter`
- **Expected**: send triggered once

---

## Settings / toggles

### TC-SET-001 — Mode switch (offline/assist) updates URL and UI
- **Type**: e2e
- **Mocks**: `pywebview.api.set_poly_mode` resolves ok
- **Expected**: URL hash updated, assist elements hidden in offline

### TC-SET-002 — Detach Assist window calls open_assist_window
- **Type**: unit (Python) + e2e smoke
- **Mocks**: in e2e: stub `pywebview.api.open_assist_window` and verify call

### TC-SET-003 — Windows tile calls tile_windows
- **Type**: unit (Python) + e2e smoke
- **Mocks**: stub `tile_windows`

### TC-SET-004 — Claude terminal openwin calls launch_claude_terminal_window
- **Type**: unit (Python signature) + e2e smoke
- **Risk**: prevents “2 args given” regression

### TC-SET-005 — Remember checkbox persists poly_mode to localStorage

- **Type**: e2e
- **Preconditions**: page loaded in assist mode
- **Steps**:
  - open settings
  - check `#settings_poly_mode_remember`
- **Expected**: `localStorage.getItem(“polyphonia_poly_mode”)` equals current poly_mode (`assist`)
- **Risk**: core behaviour of the remember-session feature

### TC-SET-006 — Unchecking remember clears localStorage entry

- **Type**: e2e
- **Preconditions**: `polyphonia_poly_mode` already set in localStorage
- **Steps**:
  - open settings (checkbox reflects saved state)
  - uncheck `#settings_poly_mode_remember`
- **Expected**: `localStorage.getItem(“polyphonia_poly_mode”)` is `null`
- **Risk**: prevents stale saved mode after user opts out

### TC-SET-007 — Saved mode restored from localStorage on page load

- **Type**: e2e
- **Preconditions**: `polyphonia_poly_mode = “offline”` injected into localStorage before page boots; URL hash contains `poly_mode=assist`
- **Steps**: load page
- **Expected**: `html` element has class `poly_mode_offline` (saved mode wins over URL hash)
- **Risk**: ensures the boot restore path actually fires and overrides URL

---

## renderAssistBody — code-block rendering

### TC-RENDER-001 — Standard fenced block splits into 3 parts with fence detected

- **Type**: e2e (JS regex evaluation)
- **Input**: `"Hello\n` `` ``` `` `xml\n<note>C</note>\n` `` ``` `` `\nWorld"`
- **Expected**: `parts.length === 3`, fence part detected
- **Risk**: core code-block rendering; regressions print raw backtick markup

### TC-RENDER-002 — CRLF line endings normalised before fence detection

- **Type**: e2e (JS regex evaluation)
- **Input**: same text with `\r\n` instead of `\n`
- **Expected**: after normalisation, `parts.length === 3`, fence found
- **Risk**: Windows-originated GPT responses silently fail without normalisation

### TC-RENDER-003 — Unclosed fence produces a degradable part, not raw text

- **Type**: e2e (JS regex evaluation)
- **Input**: `"intro\n` `` ``` `` `python\nprint('hello')"` (no closing fence)
- **Expected**: `has_unclosed === true` (JS fallback branch handles it)
- **Risk**: streaming/partial GPT responses should degrade gracefully

### TC-RENDER-004 — Plain text produces no fence parts

- **Type**: e2e (JS regex evaluation)
- **Input**: plain sentence without backticks
- **Expected**: `parts.length === 1`, `any_fence === false`
- **Risk**: regression guard — plain messages must not hit code-block path

---

## Python API (phrygian_app.py) — negative paths

### TC-PY-001 — launch_main invalid_json
- **Type**: unit
- **Steps**: call `launch_main("not json")`
- **Expected**: `ok:false`, `error=invalid_json`

### TC-PY-002 — launch_main invalid_mode
- **Type**: unit
- **Expected**: `ok:false`, `error=invalid_mode`

### TC-PY-003 — launch_main index_not_found returns clear message (no navigation)
- **Type**: unit
- **Mocks**: patch `get_resource_base()` to temp dir without index.html
- **Expected**: `ok:false`, `error=index_not_found`, message includes computed base

### TC-PY-004 — openai_chat missing key returns missing_api_key
- **Type**: unit
- **Mocks**: clear env + session keys

### TC-PY-005 — openai_chat HTTP error maps to ok:false + message
- **Type**: unit
- **Mocks**: `urllib.request.urlopen` raises `HTTPError` with body containing `error.code`

---

## Build & exe (PyInstaller)

### TC-BUILD-001 — pyinstaller build succeeds
- **Type**: build
- **Command**: `pyinstaller polyphonia.spec`
- **Expected**: exit code 0, `dist/polyphonia.exe` exists

### TC-BUILD-002 — exe resources resolve (onedir/onefile)
- **Type**: unit (frozen simulation) + build
- **Expected**: `get_resource_base()` points to location with index/assets

### TC-BUILD-003 — exe smoke run starts window
- **Type**: build/manual (automation depends on runner)
- **Expected**: process lives > N seconds OR exposes a minimal headless signal
- **Mocks**: none

---

## AI framework / riff_contract

### TC-RIFF-001 — schema validates example
- **Type**: unit/contract
- **Inputs**: `qa/examples/riff-fragment-v0.example.json` vs `docs/schemas/riff-fragment-v0.schema.json`
- **Expected**: validation passes

### TC-RIFF-002 — validator rejects malformed payload
- **Type**: unit
- **Expected**: clear error; deterministic failure

