"""tasks/items の単一選択リスト属性を検証する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from task_properties import SINGLE_CHOICE_FIELDS
from task_source_links import as_str, is_routine_task, uses_legacy_source_fields

TASKS_DIR = Path(__file__).resolve().parent.parent
ITEMS_DIR = TASKS_DIR / "items"

# 移行完了後は False にし、非ルーティーンの旧 source_* を禁止する。
ALLOW_LEGACY_SOURCE = False

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


def validate_pointer_pairs(
    rel: str,
    data: dict,
    id_key: str,
    url_key: str,
    updated_key: str,
    label: str,
) -> list[str]:
    errors: list[str] = []
    id_value = as_str(data.get(id_key))
    url_value = as_str(data.get(url_key))
    updated_value = as_str(data.get(updated_key))

    if id_value and not url_value:
        errors.append(f"{rel}: {label} の id があるとき url が必要です")
    if url_value and not id_value:
        errors.append(f"{rel}: {label} の url があるとき id が必要です")
    if updated_value and not id_value:
        errors.append(f"{rel}: {label} の updated_at だけが設定されています")

    return errors


def validate_source_shape(rel: str, data: dict) -> list[str]:
    errors: list[str] = []

    if is_routine_task(data):
        if as_str(data.get("github_id")) or as_str(data.get("backlog_id")):
            errors.append(f"{rel}: ルーティーンに github_* / backlog_* を設定できません")
        if ALLOW_LEGACY_SOURCE and uses_legacy_source_fields(data):
            errors.append(f"{rel}: ルーティーンに旧 source_id を設定できません")
        return errors

    github_type = data.get("github_type")
    if github_type is not None:
        errors.extend(validate_value("github_type", github_type, SINGLE_CHOICE_FIELDS["github_type"]))

    errors.extend(
        validate_pointer_pairs(rel, data, "github_id", "github_url", "github_updated_at", "GitHub")
    )
    errors.extend(
        validate_pointer_pairs(rel, data, "backlog_id", "backlog_url", "backlog_updated_at", "Backlog")
    )

    gh_type = data.get("github_type")
    gh_type_val = gh_type[0] if isinstance(gh_type, list) and len(gh_type) == 1 else ""
    gh_id = as_str(data.get("github_id"))
    if gh_type_val and not gh_id:
        errors.append(f"{rel}: github_type があるとき github_id が必要です")
    if gh_id and not gh_type_val:
        errors.append(f"{rel}: github_id があるとき github_type が必要です")

    if ALLOW_LEGACY_SOURCE:
        if uses_legacy_source_fields(data):
            legacy_type = data.get("source_type")
            if legacy_type is not None:
                errors.extend(
                    validate_value("source_type", legacy_type, SINGLE_CHOICE_FIELDS["source_type"])
                )
    else:
        if uses_legacy_source_fields(data):
            errors.append(f"{rel}: 旧 source_type / source_id は使えません")
        source_type = data.get("source_type")
        if source_type is not None and source_type != []:
            from task_properties import single_choice

            st = single_choice(source_type)
            if st and st != "routine":
                errors.append(f"{rel}: 非ルーティーンで source_type に {st} は使えません")

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
        if key == "github_type" and data.get(key) is None:
            continue
        if key == "source_type" and data.get(key) is None and not is_routine_task(data):
            continue
        for message in validate_value(key, data.get(key), allowed):
            errors.append(f"{rel}: {message}")

    errors.extend(validate_source_shape(rel, data))

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
