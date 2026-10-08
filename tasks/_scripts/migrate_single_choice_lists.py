"""tasks/items の status / priority / source_type を単一選択リスト形式へ移行する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from task_properties import SINGLE_CHOICE_FIELDS, single_choice

TASKS_DIR = Path(__file__).resolve().parent.parent
ITEMS_DIR = TASKS_DIR / "items"

FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
KEY_LINE = re.compile(r"^([a-z_]+):\s*(.*)$")


def yaml_scalar(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value
    return yaml.safe_dump(value, allow_unicode=True).strip()


def format_key_block(key: str, value: str) -> str:
    if not value:
        return f"{key}: []"
    return f"{key}:\n  - {yaml_scalar(value)}"


def strip_key_block(lines: list[str], key: str) -> list[str]:
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        matched = KEY_LINE.match(line)
        if matched and matched.group(1) == key:
            index += 1
            while index < len(lines) and lines[index].startswith("  - "):
                index += 1
            continue
        out.append(line)
        index += 1
    return out


def insert_key_block(lines: list[str], key: str, block: str) -> list[str]:
    block_lines = block.split("\n")
    for index, line in enumerate(lines):
        matched = KEY_LINE.match(line)
        if matched and matched.group(1) == key:
            return lines[:index] + block_lines + lines[index + 1 :]

    insert_at = len(lines)
    for index, line in enumerate(lines):
        matched = KEY_LINE.match(line)
        if matched and matched.group(1) == "estimate":
            insert_at = index + 1
            break

    return lines[:insert_at] + block_lines + lines[insert_at:]


def migrate_frontmatter(fm_text: str) -> str:
    data = yaml.safe_load(fm_text) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter がマッピングではありません")

    lines = fm_text.split("\n")
    for key in SINGLE_CHOICE_FIELDS:
        value = single_choice(data.get(key))
        if data.get(key) is not None and not isinstance(data.get(key), (str, list)):
            value = ""
        if isinstance(data.get(key), list) and len(data.get(key)) > 1:
            value = ""
        block = format_key_block(key, value)
        lines = strip_key_block(lines, key)
        lines = insert_key_block(lines, key, block)

    return "\n".join(lines)


def migrate_file(path: Path, dry_run: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    match = FM_PATTERN.match(text)
    if not match:
        return False

    new_fm = migrate_frontmatter(match.group(1))
    if new_fm == match.group(1):
        return False

    new_text = f"---\n{new_fm}\n---\n{text[match.end():]}"
    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    changed = 0
    for path in sorted(ITEMS_DIR.rglob("*.md")):
        if migrate_file(path, dry_run=args.dry_run):
            changed += 1
            print(path.relative_to(TASKS_DIR.parent))

    print(f"Migrated {changed} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
