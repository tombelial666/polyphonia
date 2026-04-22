from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    source = root / "AGENTS.md"
    target = root / "CLAUDE.md"

    if not source.exists():
        return

    source_text = source.read_text(encoding="utf-8")
    marker = "# PETS Agent Guide"
    if source_text.startswith(marker):
        source_text = source_text[len(marker) :].lstrip()

    next_text = (
        "# PETS Agent Guide\n\n"
        "This file is synchronized from `AGENTS.md` by `scripts/sync_docs.py`.\n\n"
        f"{source_text}"
    )

    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current != next_text:
        target.write_text(next_text, encoding="utf-8")


if __name__ == "__main__":
    main()
