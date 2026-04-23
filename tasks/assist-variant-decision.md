# Assist / riff pipeline — variant decision (implementation)

## Confirmed

- **UI variant (MVP):** **A** — встроенная панель ассистента в собранном `index.html` (кнопка открытия, черновики, подтверждение перед «применить»-демо). Отдельная страница (**B**) и отдельный HTTP-сервер (**C**) — **deferred**; минимальный «backend» для LLM уже есть **внутри `phrygian_app.py` + `js_api`** (без отдельного порта).
- **LLM policy (MVP):** **гибрид** — при старте лаунчера выбирается **`POLYPHONIA_MODE`**: `offline` (без Assist/GPT) или `assist` (панель Assist + OpenAI при ключе). Ключ OpenAI: **`OPENAI_API_KEY`** или сессия в RAM через `set_openai_api_key`. Привилегированный CLI репозитория использует тот же класс секрета **`PETS_OPERATOR_TOKEN`** (см. `docs/dev-notes/repo-admin-cli.md`). Контекст инструмента в GPT — только при **галочке**. Системный промпт допускает творческие вопросы без копирования чужих табов. См. [docs/dev-notes/openai-assist-bridge.md](../docs/dev-notes/openai-assist-bridge.md).
- **Bridge:** `window.polyphonia` в [assets/polyphonia_ui.js](../assets/polyphonia_ui.js) — `getInstrumentContext`, `exportMusicXMLScaleSnapshot`, `exportSession` (localStorage stub), `openAssist`, `setFullscreen` (pywebview `js_api` + Fullscreen API fallback); при наличии pywebview — также `openai_chat` / `set_openai_api_key` на объекте `js_api`.

## Assumption

- Для E2E и CI достаточно проверки DOM панели и экспорта MusicXML без реального LLM.

## Risk

- Расширение `build_index.py` остаётся точкой сборки; при дальнейшем росте UI — вынести шаблоны (roadmap Phase 1).

## Committed change record

- **2026-04-23:** зафиксированы вариант **A** и политика LLM; реализация см. `assets/polyphonia_ui.js`, `build_index.py`, `phrygian_app.py`, `tasks/polyphonia-modernization-roadmap.md`, `docs/schemas/riff-fragment-v0.schema.json`, `riff_contract/`, каталог сессий `polyphonia_sessions/` (gitignore).
- **2026-04-24:** опциональный вызов **OpenAI Chat Completions** из Assist через `PolyphoniaApi.openai_chat` / `set_openai_api_key`; дока `docs/dev-notes/openai-assist-bridge.md`; UI «Спросить GPT» в панели Assist.
