# Follow-up: riff_apply + riff_contract

## Objective

После доработок Assist/GPT — отдельный трек: **идея пользователя → детерминированное применение на грифе** и артефакты в `riff_contract/` / `polyphonia_sessions/` (human-in-the-loop).

## Confirmed (источник правды)

- Каркас и чеклист: [`tasks/polyphonia-modernization-roadmap.md`](polyphonia-modernization-roadmap.md).
- Схема: [`docs/schemas/riff-fragment-v0.schema.json`](../docs/schemas/riff-fragment-v0.schema.json).
- Политика: [`tasks/assist-variant-decision.md`](assist-variant-decision.md).

## Next steps (черновик)

1. Зафиксировать текущий поток `__poly_riff_draft` и кнопки Apply в UI.
2. Минимальный сценарий: черновик → валидация по схеме → подсветка только из детерминированных данных грифа.
3. Unit + e2e smoke под новый сценарий.

## Deferred

- Вариант B (ключ OpenAI только в «Настройки») — см. [`docs/dev-notes/assist-llm-login-ux.md`](../docs/dev-notes/assist-llm-login-ux.md).
