# Repository Index

## Core Project Files

- `README.md` - entry point and project overview
- `MANIFEST.md` - identity, scope, and decision boundaries
- `STRUCTURE.md` - repository layer model
- `AGENTS.md` - agent-facing guide
- `CLAUDE.md` - mirrored agent-facing guide

## Runtime Files

- `phrygian_app.py` - desktop launcher; startup `POLYPHONIA_MODE` (offline vs assist) and `?poly_mode=` URL
- `build_index.py` - current HTML assembly helper (также пишет `run_polyphonia.bat` / `run_polyphonia.ps1`; на Windows — ярлык **Polyphonia** на рабочем столе)
- `run_polyphonia.bat` / `run_polyphonia.ps1` — запуск `python phrygian_app.py` из корня (пересобираются при `python build_index.py`)
- `assets/polyphonia_startup.html` — стартовое окно режима ONLINE/OFFLINE и ключей
- `assets/polyphonia_launcher_icon.png` / `assets/polyphonia_app_icon.ico` — иконка (ICO собирается `build_index.py` при установленном Pillow)
- `index.html` - runnable page
- `assets/` - static logic, data, CSS, and media
- `assets/polyphonia_ui.js` - assist panel, layout presets, string visibility, fingering hints, MusicXML snapshot helper, `window.polyphonia` bridge
- `polyphonia.spec` - current packaging path (desktop app **Polyphonia**)
- `riff_contract/` - Python helper validating riff-fragment JSON against `docs/schemas/riff-fragment-v0.schema.json`
- `docs/schemas/riff-fragment-v0.schema.json` - riff fragment JSON Schema v0
- `qa/examples/riff-fragment-v0.example.json` - example fragment for tests and manual QA
- `docs/dev-notes/ai-framework-reaper-spike.md` - local notes on `C:\ai-framework-reaper` reuse (not external SOT)
- `docs/dev-notes/openai-assist-bridge.md` - optional OpenAI GPT via `phrygian_app.py` / pywebview `js_api`
- `docs/dev-notes/assist-llm-login-ux.md` - GPT vs Claude «логин», UX и варианты улучшений
- `polyphonia_sessions/dialogs/` - Markdown-лог Assist (gitignore); метки User / System (UI) / GPT (OpenAI) / GPT (ошибка) в заголовках
- `tasks/assist-variant-decision.md` - committed Assist variant and LLM policy note

## AI Workflow Files

- `.cursor/rules/` - active Cursor rules
- `.cursor/skills/` - curated PETS skills
- `.cursor/agents/` - curated PETS agent roles
- `.cursor/commands/` - minimal command helpers
- `.cursor/hooks.json` - sync hooks
- `.claude/` - mirrored adapter layer
- `scripts/repo_admin_cli.py` - subprocess runner (`PETS_OPERATOR_TOKEN`, cwd = repo root)
- `scripts/claude_terminal.py` - ANSI banner then `exec` into Claude Code CLI (`claude` on PATH); see `docs/dev-notes/claude-terminal-launcher.md`
- `docs/dev-notes/repo-admin-cli.md` - usage and safety for admin CLI
- `scripts/sync_docs.py` - sync `AGENTS.md` to `CLAUDE.md`
- `scripts/sync_configs.py` - sync `.cursor` to `.claude`

## Docs And Task Files

- `docs/architecture.md`
- `docs/desktop-transition-roadmap.md`
- `docs/ai-foundation-bootstrap.md`
- `docs/legacy-index.md`
- `docs/legacy-assets-index.md`
- `docs/legacy-reference-index.md`
- `docs/dev-workflow/commands-reference.md`
- `docs/documentation-standard.md`
- `docs/adr/`
- `docs/templates/`
- `tasks/_template.md`
- `tasks/polyphonia-modernization-roadmap.md`
- `repo-index.yaml`
- `impact-map.yaml`

## Non-Core Reference Artifacts

- `A Phrygian Dominant.html`
- `A Phrygian Dominant.spec`
- `A Phrygian Dominant_files/`

These are reference leftovers and should not be treated as core project truth.
