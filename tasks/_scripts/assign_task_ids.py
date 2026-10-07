"""個人タスクに通し番号 id を付与し、タスクツリーの表示名を揃える。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

WIKILINK_RE = re.compile(r"(\[\[(.*?)(?:\|(.*?))?\]\])")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", flags=re.DOTALL)
TASK_ID_KEY = "task_id"
LEGACY_TASK_ID_LINE = re.compile(r"^id:\s*(\d+)\s*$", flags=re.MULTILINE)
TASK_ID_LINE = re.compile(r"^task_id:\s*\d+\s*$", flags=re.MULTILINE)


def load_task_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)

    if not match:
        return None

    data = yaml.safe_load(match.group(1)) or {}

    if not isinstance(data, dict):
        return None

    data["_path"] = path
    data["_text"] = text
    return data


def task_vault_path(task: dict, vault_root: Path) -> str:
    rel = task["_path"].resolve().relative_to(vault_root.resolve()).as_posix()

    if rel.endswith(".md"):
        rel = rel[:-3]

    return rel


def normalize_task_id(value) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        return parsed if parsed > 0 else None

    return None


def task_id_value(task: dict) -> int | None:
    return normalize_task_id(task.get(TASK_ID_KEY))


def display_alias(task: dict) -> str:
    title = str(task.get("title") or "").strip()
    task_id = task_id_value(task)

    if task_id is not None:
        return f"{task_id} {title}"

    return title


def migrate_legacy_task_id_field(text: str) -> tuple[str, bool]:
    match = FRONTMATTER_RE.match(text)

    if not match:
        return text, False

    frontmatter = match.group(1)
    body = text[match.end():]

    if TASK_ID_LINE.search(frontmatter):
        new_frontmatter, count = LEGACY_TASK_ID_LINE.subn("", frontmatter)

        if count == 0:
            return text, False

        new_frontmatter = new_frontmatter.strip("\n")
        return f"---\n{new_frontmatter}\n---\n{body}", True

    legacy = LEGACY_TASK_ID_LINE.search(frontmatter)

    if legacy is None:
        return text, False

    new_frontmatter = LEGACY_TASK_ID_LINE.sub(
        lambda match: f"task_id: {match.group(1)}",
        frontmatter,
        count=1,
    )
    return f"---\n{new_frontmatter}\n---\n{body}", True


def migrate_legacy_task_ids(items_dir: Path) -> int:
    migrated = 0

    for path in sorted(items_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        new_text, changed = migrate_legacy_task_id_field(text)

        if changed:
            path.write_text(new_text, encoding="utf-8", newline="\n")
            migrated += 1

    return migrated


def load_all_tasks(items_dir: Path) -> list[dict]:
    tasks = []

    for path in sorted(items_dir.rglob("*.md")):
        task = load_task_file(path)

        if task:
            tasks.append(task)

    return tasks


def validate_ids(tasks: list[dict]) -> None:
    seen: dict[int, Path] = {}

    for task in tasks:
        path = task["_path"]
        raw = task.get(TASK_ID_KEY)

        if raw is None:
            continue

        task_id = normalize_task_id(raw)

        if task_id is None:
            raise ValueError(f"task_id が正の整数ではありません: {path}")

        if task_id in seen:
            raise ValueError(
                f"task_id {task_id} が重複しています: {seen[task_id]} と {path}"
            )

        seen[task_id] = path


def load_next_id(config_path: Path) -> int:
    if not config_path.exists():
        return 1

    data = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"{config_path} の形式が不正です")

    next_id = data.get("next_id", 1)

    if not isinstance(next_id, int) or isinstance(next_id, bool) or next_id < 1:
        raise ValueError(f"{config_path} の next_id が不正です")

    return next_id


def save_next_id(config_path: Path, next_id: int) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps({"next_id": next_id}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_tree_paths(tree_path: Path, vault_root: Path) -> list[str]:
    if not tree_path.exists():
        return []

    text = tree_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    try:
        tree_start = lines.index("## タスクツリー")
    except ValueError:
        return []

    tree_end = len(lines)

    for index in range(tree_start + 1, len(lines)):
        if lines[index].startswith("## "):
            tree_end = index
            break

    ordered: list[str] = []
    seen: set[str] = set()

    for line in lines[tree_start:tree_end]:
        for match in WIKILINK_RE.finditer(line):
            link_path = match.group(2).replace("\\", "/")

            if link_path.endswith(".md"):
                link_path = link_path[:-3]

            if link_path not in seen:
                seen.add(link_path)
                ordered.append(link_path)

    return ordered


def order_tasks_for_assignment(
    tasks: list[dict],
    tree_path: Path,
    vault_root: Path,
) -> list[dict]:
    path_to_task = {task_vault_path(task, vault_root): task for task in tasks}
    tree_paths = parse_tree_paths(tree_path, vault_root)
    ordered: list[dict] = []
    seen: set[str] = set()

    for path in tree_paths:
        task = path_to_task.get(path)

        if task is not None and path not in seen:
            seen.add(path)
            ordered.append(task)

    remaining = sorted(
        [task for task in tasks if task_vault_path(task, vault_root) not in seen],
        key=lambda t: task_vault_path(t, vault_root),
    )

    return ordered + remaining


def insert_id_into_frontmatter(text: str, task_id: int) -> str:
    match = FRONTMATTER_RE.match(text)

    if not match:
        raise ValueError("frontmatter がありません")

    body_start = match.end()
    frontmatter = match.group(1)

    if re.search(r"^task_id:\s*", frontmatter, flags=re.MULTILINE):
        return text

    new_frontmatter = f"task_id: {task_id}\n{frontmatter}"
    return f"---\n{new_frontmatter}\n---\n{text[body_start:]}"


def rewrite_tree_aliases(tree_path: Path, tasks: list[dict], vault_root: Path) -> bool:
    if not tree_path.exists():
        return False

    path_to_alias = {
        task_vault_path(task, vault_root): display_alias(task) for task in tasks
    }
    original = tree_path.read_text(encoding="utf-8")
    text = original.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    try:
        tree_start = lines.index("## タスクツリー")
    except ValueError:
        return False

    tree_end = len(lines)

    for index in range(tree_start + 1, len(lines)):
        if lines[index].startswith("## "):
            tree_end = index
            break

    changed = False

    for index in range(tree_start, tree_end):
        line = lines[index]

        def replace_link(match: re.Match) -> str:
            nonlocal changed
            full = match.group(1)
            link_path = match.group(2).replace("\\", "/")

            if link_path.endswith(".md"):
                link_path = link_path[:-3]

            alias = path_to_alias.get(link_path)

            if alias is None:
                return full

            new_link = f"[[{match.group(2)}|{alias}]]"

            if new_link != full:
                changed = True

            return new_link

        new_line = WIKILINK_RE.sub(replace_link, line)

        if new_line != line:
            lines[index] = new_line

    if not changed:
        return False

    tree_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return True


def assign(tasks_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    items_dir = tasks_dir / "items"
    tree_path = tasks_dir / "_タスク.md"
    config_path = tasks_dir / "_config" / "task-id.json"
    vault_root = tasks_dir.parent

    if not dry_run:
        migrated = migrate_legacy_task_ids(items_dir)

        if migrated:
            print(f"Migrated legacy id to task_id on {migrated} file(s).")

    tasks = load_all_tasks(items_dir)
    validate_ids(tasks)

    max_existing = 0

    for task in tasks:
        task_id = task_id_value(task)

        if task_id is not None:
            max_existing = max(max_existing, task_id)

    cursor = max(load_next_id(config_path), max_existing + 1)
    ordered = order_tasks_for_assignment(tasks, tree_path, vault_root)
    assigned_count = 0

    for task in ordered:
        if task_id_value(task) is not None:
            continue

        if dry_run:
            task[TASK_ID_KEY] = cursor
            cursor += 1
            assigned_count += 1
            continue

        new_text = insert_id_into_frontmatter(task["_text"], cursor)
        task["_path"].write_text(new_text, encoding="utf-8", newline="\n")
        task[TASK_ID_KEY] = cursor
        cursor += 1
        assigned_count += 1

    if not dry_run and assigned_count:
        save_next_id(config_path, cursor)

    if not dry_run:
        rewrite_tree_aliases(tree_path, tasks, vault_root)

    return assigned_count, cursor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="個人タスクに通し番号 id を付与する")
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="tasks ディレクトリ",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルを書き換えずに採番のみ検証する",
    )
    args = parser.parse_args(argv)

    try:
        assigned, next_id = assign(args.tasks_dir, dry_run=args.dry_run)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Dry run: would assign {assigned} id(s). next_id would be {next_id}.")
    else:
        print(f"Assigned {assigned} id(s). next_id is {next_id}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
