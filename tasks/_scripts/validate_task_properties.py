"""tasks/items の単一選択リスト属性を検証する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from task_properties import SINGLE_CHOICE_FIELDS

TASKS_DIR = Path(__file__).resolve().parent.parent
ITEMS_DIR = TASKS_DIR / "items"

FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def validate_value(key: str, value, allowed: frozenset[str]) -> list[str]:
    errors: list[str] = []
    label = key

    if value is None:
        errors.append(f"{label} がありません")
        return errors

    if not isinstance(value, list):
        errors.append(f"{label} はリストで指定してください")
        return errors

    if len(value) > 1:
        errors.append(f"{label} は0件または1件だけ指定できます")
        return errors

    if len(value) == 1:
        item = value[0]
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label} の要素は空でない文字列にしてください")
        elif item not in allowed:
            errors.append(f"{label} の値が不正です: {item}")

    return errors


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = FM_PATTERN.match(text)
    if not match:
        return ["frontmatter がありません"]

    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return [f"YAML が読めません: {exc}"]

    if not isinstance(data, dict):
        return ["frontmatter がマッピングではありません"]

    errors: list[str] = []
    rel = path.as_posix()
    for key, allowed in SINGLE_CHOICE_FIELDS.items():
        for message in validate_value(key, data.get(key), allowed):
            errors.append(f"{rel}: {message}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    all_errors: list[str] = []
    for path in sorted(ITEMS_DIR.rglob("*.md")):
        all_errors.extend(validate_file(path))

    if all_errors:
        for message in all_errors:
            print(message, file=sys.stderr)
        return 1

    print(f"Validated {len(list(ITEMS_DIR.rglob('*.md')))} task file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
