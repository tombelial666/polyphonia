# PETS AI Workflow Reference

This is a minimal adapted workflow inspired by donor projects, reduced for PETS.

## Core Flow

`discover -> plan -> implement -> review -> docs`

## Commands And Intent

| Stage | Purpose | Main Output |
|---|---|---|
| `discover` | clarify a feature, workflow, or product idea | task discovery note |
| `plan` | define the smallest safe implementation path | technical task note |
| `implement` | make the change with source-of-truth awareness | code/data/docs changes |
| `review` | check correctness, risk, and documentation fit | review findings |
| `docs` | update manifest, architecture, workflow, and changelog docs | updated documentation |

## PETS-Specific Rules

- Always identify the source-of-truth file before editing.
- If a change affects project direction, update `MANIFEST.md` and related docs.
- Keep current `pywebview` runtime and desktop-shell roadmap clearly separated.
- Prefer deterministic data or explicit review over speculative automation.

## Specialist Domain Roles

PETS can use narrow music-domain specialists inside the same minimal AI framework:

- `music-director` for mixed or cross-domain music tasks
- `composer` for constrained composition options
- `music-theory-teacher` for theory explanation and examples
- `producer` for arrangement and production direction
- `solfege-teacher` for graded ear-training and sight-singing drills

These specialists can share reusable instrument-aware skills:

- `guitar-guidance`
- `piano-guidance`
- `bass-guidance`
- `drums-guidance`
- `strings-guidance`
- `voice-guidance`

These specialists should:

- work from explicit inputs and say what is assumed
- return reviewable options rather than overconfident final answers
- avoid claiming audio certainty, authorship guarantees, or unverifiable stylistic facts

## Implementation Variants

### Variant A - Specialist Prompt Library

Use separate prompt roles plus paired skills for each musical job. This is the current PETS default because it keeps rollout simple, reviewable, and aligned with the existing minimal adapter layer.

### Variant B - Conductor Plus Specialists

Add a coordinator that routes work to the right specialist and merges results. PETS now supports a lightweight prompt-level version of this through `music-director`, but not a heavy autonomous orchestration stack.

### Variant C - Evaluation-Backed Specialists

Keep the specialist roles, but add reusable rubrics, example prompts, and regression checks for musical quality and honesty. This is the strongest long-term pattern, but not the lightest first rollout.

## Music Command Shortcuts

The adapter layer can expose focused helper commands for common music tasks:

- `music-task` for orchestration-lite across specialists
- `compose-idea` for composition support
- `theory-lesson` for theory explanation
- `production-pass` for arrangement and production feedback
- `solfege-drill` for ear-training and sight-singing exercises

## Typical Lightweight Sequence

1. Create or update a task note in `tasks/`
2. Inspect affected source files
3. Use `music-director` when a music task spans multiple specialist viewpoints
4. Apply a specialist role if the task benefits from narrow domain expertise
5. Pull in a reusable instrument skill if voicing, range, fingering, or playability matters
6. Make the smallest useful change
7. Review output and update docs if needed
8. Sync adapter layers if `.cursor/` or `AGENTS.md` changed

## Polyphonia и репозиторий — шпаргалка терминала

Оформлено как краткий **runbook**: одна страница, без дублирования длинных спеков (детали — в `docs/dev-notes/repo-admin-cli.md` и `docs/dev-notes/openai-assist-bridge.md`).

> **Безопасность:** реальные ключи и токены не вставляй в чаты и не коммить. Ниже — только плейсхолдеры; значения задаёшь локально в своей сессии PowerShell.

### Переменные окружения (по необходимости)

| Переменная | Назначение |
|------------|------------|
| `PETS_OPERATOR_TOKEN` | Непустая строка — «операторский» пропуск для `scripts/repo_admin_cli.py` (только из **корня** репозитория) |
| `OPENAI_API_KEY` | Доступ к GPT из Assist в режиме **`assist`** (серверный вызов из `phrygian_app.py`) |
| `POLYPHONIA_MODE` | `offline` или `assist` — пропуск интерактивного вопроса при запуске `python phrygian_app.py` |
| `OPENAI_MODEL` | Необязательно; иначе мост использует модель по умолчанию из кода |
| `POLYPHONIA_TRACE` | `1` включает расширенную трассировку запросов GPT: correlation id и цепочку UI → Python → HTTP → UI в консольных логах |

### Сборка UI, тесты, запуск оболочки

```powershell
Set-Location D:\Reps\PETS   # свой путь к клону

$env:PETS_OPERATOR_TOKEN = "<секрет>"
$env:POLYPHONIA_MODE = "assist"
# $env:OPENAI_API_KEY = "sk-..."

python build_index.py
# после этого: run_polyphonia.bat / run_polyphonia.ps1 в корне; на Windows — ярлык Polyphonia.lnk на рабочем столе
python -m pytest --tb=short
python phrygian_app.py
```

При запуске `phrygian_app.py` **без** заданного `POLYPHONIA_MODE` и **с** интерактивной консолью появится вопрос: **1** — офлайн (без Assist/GPT), **2** — с ассистентами. Без TTY по умолчанию выбирается офлайн.

### Только `index.html` в браузере

Путь `file:///.../index.html` без параметров в приложении даёт режим **офлайн** в JS. Чтобы открыть интерфейс с Assist, добавь в URL: **`#poly_mode=assist`** (так же сделано в E2E). В окне **phrygian_app.py** режим **офлайн / assist** можно сменить в **«Настройки»** (без перезапуска процесса); новый холодный старт снова из `POLYPHONIA_MODE` / меню.

Опциональный лог диалога Assist в Markdown: кнопка **Настройки** → чекбокс; файлы в **`polyphonia_sessions/dialogs/`** (см. `docs/dev-notes/openai-assist-bridge.md`).

Сводка «логина» GPT/Claude и варианты развития UX: **`docs/dev-notes/assist-llm-login-ux.md`**.

### Claude Code — «навороченный» терминал (баннер + `exec`)

Из корня репозитория: сначала цветной баннер (рамка, ветка git), затем запуск настоящего **`claude`** из PATH без лишней оболочки.

```powershell
Set-Location D:\Reps\PETS
python scripts/claude_terminal.py
python scripts/claude_terminal.py chat
python scripts/claude_terminal.py --banner-only
```

Подробности: `docs/dev-notes/claude-terminal-launcher.md`. Без цветов: `$env:NO_COLOR = "1"`.

### Admin CLI (одна команда из корня)

```powershell
Set-Location D:\Reps\PETS
$env:PETS_OPERATOR_TOKEN = "<секрет>"
python scripts/repo_admin_cli.py -- git status
```

## QA change gate

- Canonical procedure: `docs/dev-workflow/qa-change-gate.md`
- Cursor command helper: `.cursor/commands/qa-change-gate.md`
- Reviewer agent: `qa-change-gate-reviewer`
- GitHub Actions: `.github/workflows/ci.yml` (change gate + E2E)
