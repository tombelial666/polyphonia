from pathlib import Path
import shutil


SKIP_NAMES = {"hooks.json"}


def copy_recursive(source: Path, target: Path) -> None:
    if source.is_dir():
        target.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            if child.name in SKIP_NAMES:
                continue
            copy_recursive(child, target / child.name)
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    next_bytes = source.read_bytes()
    current_bytes = target.read_bytes() if target.exists() else None
    if current_bytes != next_bytes:
        shutil.copy2(source, target)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    source_root = root / ".cursor"
    target_root = root / ".claude"

    if not source_root.exists():
        return

    copy_recursive(source_root, target_root)


if __name__ == "__main__":
    main()
