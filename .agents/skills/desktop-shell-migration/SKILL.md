---
name: desktop-shell-migration
description: Use when planning or evaluating a transition from the current PETS pywebview runtime toward a future Electron or Tauri shell.
---

# Desktop Shell Migration

## Goal

Support desktop-shell planning without pretending the migration is already done.

## Workflow

1. Describe the current runtime path first.
2. Identify which parts are authored sources and which are runnable outputs.
3. Separate immediate changes from roadmap changes.
4. Prefer adapter and boundary improvements before shell replacement.

## Questions To Answer

- What should remain static data?
- What should become a cleaner web app source?
- What bridge or shell APIs would be needed later?
- What packaging path is simplest for PETS?
