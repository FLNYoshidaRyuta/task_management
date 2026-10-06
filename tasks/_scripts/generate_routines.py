"""ルーティーン定義から、期日ごとの個人タスクを生成する。"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

RECURRENCES = ("daily", "weekly", "monthly", "weekdays")
PRIORITIES = ("Critical", "High", "Mid", "Low")
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
FORBIDDEN_TITLE_CHARS = set('<>:"/\\|?*#^')


@dataclass
class ChildTemplate:
    id: str
    title: str
    priority: str
    estimate: str
    depends_on: list[str]
    body: str


@dataclass
class Routine:
    path: Path
    id: str
    title: str
    project: str
    recurrence: str
    weekday: int | None
    day: int | None
    priority: str
    estimate: str
    generate_before_days: int
    enabled: bool
    children: list[ChildTemplate]
    body: str


@dataclass
class GenerateResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def read_document(path: Path, required: bool = True):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.DOTALL)

    if not match:
        if required:
            raise ValueError("frontmatter がありません")

        return None, None

    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML が読めません: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("frontmatter がマッピングではありません")

    body = text[match.end():].strip("\n")
    return data, body


def as_date_str(value):
    if value is None:
        return ""

    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]

    return str(value).strip()[:10]


def yaml_scalar(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value

    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return value

    if (
        value
        and value == value.strip()
        and value.lower() not in {"null", "true", "false", "yes", "no", "~"}
        and not value.startswith(("-", "?", "{", "[", "&", "*", "!", "|", ">", "%", "@", "`"))
        and not re.search(r"[:#{}[\],&*!|>%@`'\"]", value)
    ):
        return value

    return json.dumps(value, ensure_ascii=False)


def optional_field(key: str, value: str) -> str:
    if value == "":
        return f"{key}:"

    return f"{key}: {yaml_scalar(value)}"


def validate_title(title: str, label: str, errors: list[str]):
    if any(char in title for char in FORBIDDEN_TITLE_CHARS):
        errors.append(f"{label} に使えない文字が含まれています")
        return

    if any(ord(char) < 32 for char in title):
        errors.append(f"{label} に改行や制御文字が含まれています")
        return

    if title.endswith((" ", ".")):
        errors.append(f"{label} の末尾に空白やピリオドは使えません")


def optional_text(data: dict, key: str, errors: list[str]) -> str:
    if key not in data or data[key] is None:
        return ""

    value = data[key]

    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        errors.append(f"{key} は文字列で指定してください")
        return ""

    return str(value).strip()


def optional_priority(data: dict, errors: list[str]) -> str:
    if "priority" not in data or data["priority"] is None or data["priority"] == "":
        return ""

    value = data["priority"]

    if not isinstance(value, str) or value not in PRIORITIES:
        errors.append("priority は Critical / High / Mid / Low のいずれかです")
        return ""

    return value


def require_text(data: dict, key: str, errors: list[str]) -> str:
    value = data.get(key)

    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} がありません")
        return ""

    return value.strip()


def parse_children(data: dict, errors: list[str]) -> list[ChildTemplate]:
    raw_children = data.get("children") or []

    if not isinstance(raw_children, list):
        errors.append("children はリストで指定してください")
        return []

    parsed = []

    for index, raw in enumerate(raw_children, start=1):
        label = f"children[{index}]"

        if not isinstance(raw, dict):
            errors.append(f"{label} はマッピングで指定してください")
            continue

        child_id = require_text(raw, "id", errors)
        title = require_text(raw, "title", errors)

        if child_id and not ID_PATTERN.fullmatch(child_id):
            errors.append(f"{label} の id は英数字、ハイフン、アンダースコアだけ使えます")

        if title:
            validate_title(title, f"{label} の title", errors)

        priority = optional_priority(raw, errors)
        estimate = optional_text(raw, "estimate", errors)
        body = optional_text(raw, "body", errors).strip("\n")
        depends_on = raw.get("depends_on") or []

        if not isinstance(depends_on, list) or not all(isinstance(item, str) for item in depends_on):
            errors.append(f"{label} の depends_on は文字列のリストで指定してください")
            depends_on = []

        parsed.append(
            ChildTemplate(
                id=child_id,
                title=title,
                priority=priority,
                estimate=estimate,
                depends_on=[item.strip() for item in depends_on if item.strip()],
                body=body,
            )
        )

    ids = [child.id for child in parsed if child.id]
    titles = [child.title for child in parsed if child.title]

    if len(ids) != len(set(ids)):
        errors.append("children の id が重複しています")

    if len(titles) != len(set(titles)):
        errors.append("children の title が重複しています")

    by_id = {child.id: child for child in parsed if child.id}
    by_title = {child.title: child for child in parsed if child.title}

    for child in parsed:
        resolved = []

        for dep in child.depends_on:
            id_match = by_id.get(dep)
            title_match = by_title.get(dep)

            if id_match and title_match and id_match.id != title_match.id:
                errors.append(f"{child.title} の depends_on {dep} が id と title の両方に一致します")
                continue

            if id_match:
                target = id_match.id
            elif title_match:
                target = title_match.id
            else:
                errors.append(f"{child.title} の depends_on に未知のタスクがあります: {dep}")
                continue

            if target == child.id:
                errors.append(f"{child.title} が自分自身に依存しています")
                continue

            if target not in resolved:
                resolved.append(target)

        child.depends_on = resolved

    _reject_cycles(parsed, errors)
    return parsed


def _reject_cycles(children: list[ChildTemplate], errors: list[str]):
    edges = {child.id: list(child.depends_on) for child in children if child.id}
    visiting = []
    visited = set()

    def walk(node: str):
        if node in visited or node not in edges:
            return None

        if node in visiting:
            start = visiting.index(node)
            return visiting[start:] + [node]

        visiting.append(node)

        for nxt in edges[node]:
            cycle = walk(nxt)

            if cycle:
                return cycle

        visiting.pop()
        visited.add(node)
        return None

    for node in list(edges):
        cycle = walk(node)

        if cycle:
            errors.append("children の depends_on が循環しています: " + " -> ".join(cycle))
            return


def parse_routine(path: Path):
    errors = []
    data, body = read_document(path)
    routine_id = require_text(data, "id", errors)
    title = require_text(data, "title", errors)
    project = require_text(data, "project", errors)
    recurrence = require_text(data, "recurrence", errors).lower()

    if routine_id and not ID_PATTERN.fullmatch(routine_id):
        errors.append("id は英数字、ハイフン、アンダースコアだけ使えます")

    if routine_id and path.stem != routine_id:
        errors.append("ファイル名は id と一致させてください")

    if title:
        validate_title(title, "title", errors)

    if project and ("#" in project or "^" in project or any(ord(char) < 32 for char in project)):
        errors.append("project に #、^、改行は使えません")

    if recurrence and recurrence not in RECURRENCES:
        errors.append("recurrence は daily / weekly / monthly / weekdays のいずれかです")

    weekday = None
    day = None

    if recurrence == "weekly":
        if "weekday" not in data or data["weekday"] is None:
            errors.append("weekly には weekday が必要です")
        else:
            weekday = WEEKDAYS.get(str(data["weekday"]).strip().lower())

            if weekday is None:
                errors.append("weekday は monday から sunday で指定してください")

    if recurrence == "monthly":
        raw_day = data.get("day")

        if isinstance(raw_day, bool) or not isinstance(raw_day, int):
            errors.append("monthly の day は 1 から 31 の整数で指定してください")
        elif not 1 <= raw_day <= 31:
            errors.append("monthly の day は 1 から 31 の整数で指定してください")
        else:
            day = raw_day

    raw_horizon = data.get("generate_before_days")

    if isinstance(raw_horizon, bool) or not isinstance(raw_horizon, int) or raw_horizon < 0:
        errors.append("generate_before_days は 0 以上の整数で指定してください")
        horizon = 0
    else:
        horizon = raw_horizon

    if "enabled" not in data or data["enabled"] is None:
        enabled = True
    elif isinstance(data["enabled"], bool):
        enabled = data["enabled"]
    else:
        errors.append("enabled は true または false で指定してください")
        enabled = True

    priority = optional_priority(data, errors)
    estimate = optional_text(data, "estimate", errors)
    children = parse_children(data, errors)

    if errors:
        return None, errors

    routine = Routine(
        path=path,
        id=routine_id,
        title=title,
        project=project,
        recurrence=recurrence,
        weekday=weekday,
        day=day,
        priority=priority,
        estimate=estimate,
        generate_before_days=horizon,
        enabled=enabled,
        children=children,
        body=body,
    )
    return routine, []


def load_routines(routines_dir: Path):
    if not routines_dir.exists():
        return [], []

    routines = []
    errors = []
    seen_ids = {}

    for path in sorted(routines_dir.rglob("*.md")):
        try:
            routine, file_errors = parse_routine(path)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        if file_errors:
            errors.extend(f"{path.name}: {error}" for error in file_errors)
            continue

        if routine.id in seen_ids:
            errors.append(
                f"{path.name}: id {routine.id} が {seen_ids[routine.id]} と重複しています"
            )
            continue

        seen_ids[routine.id] = path.name
        routines.append(routine)

    return routines, errors


def occurs_on(routine: Routine, day: date) -> bool:
    if routine.recurrence == "daily":
        return True

    if routine.recurrence == "weekdays":
        return day.weekday() < 5

    if routine.recurrence == "weekly":
        return day.weekday() == routine.weekday

    last_day = calendar.monthrange(day.year, day.month)[1]
    return day.day == min(routine.day, last_day)


def iter_occurrences(routine: Routine, today: date):
    last = today + timedelta(days=routine.generate_before_days)
    current = today

    while current <= last:
        if occurs_on(routine, current):
            yield current

        current += timedelta(days=1)


def index_existing(items_dir: Path):
    found = {}
    errors = []

    if not items_dir.exists():
        return found, errors

    for path in sorted(items_dir.rglob("*.md")):
        try:
            data, _body = read_document(path, required=False)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        if not data or str(data.get("source_type") or "") != "routine":
            continue

        source_id = str(data.get("source_id") or "").strip()
        routine_date = as_date_str(data.get("routine_date"))

        if not source_id or not routine_date:
            errors.append(
                f"{path.name}: source_type が routine ですが source_id または routine_date がありません"
            )
            continue

        key = (source_id, routine_date)

        if key in found:
            errors.append(f"同じルーティーンタスクが複数あります: {source_id} {routine_date}")
            continue

        found[key] = path

    return found, errors


def occurrence_path(routine_dir: Path, routine_date: date, titles: list[str]) -> Path:
    name = "_".join([routine_date.isoformat(), *titles]) + ".md"
    return routine_dir / name


def task_link(tasks_dir: Path, file_path: Path, title: str) -> str:
    vault = tasks_dir.parent.resolve()
    rel = file_path.resolve().relative_to(vault).as_posix()

    if rel.endswith(".md"):
        rel = rel[:-3]

    return f"[[{rel}|{title}]]"


def render_task(
    title: str,
    project: str,
    routine_date: date,
    priority: str,
    estimate: str,
    parent_link: str,
    depends_on: list[str],
    source_id: str,
    body: str,
) -> str:
    lines = [
        "---",
        f"title: {yaml_scalar(title)}",
        f"project: {yaml_scalar(project)}",
        "status: todo",
        f"start: {routine_date.isoformat()}",
        f"end: {routine_date.isoformat()}",
        optional_field("priority", priority),
        optional_field("estimate", estimate),
    ]

    if parent_link:
        lines.append(f"parent: {yaml_scalar(parent_link)}")
    else:
        lines.append("parent:")

    if depends_on:
        lines.append("depends_on:")
        lines.extend(f"  - {yaml_scalar(link)}" for link in depends_on)
    else:
        lines.append("depends_on: []")

    lines.extend(
        [
            "",
            "source_type: routine",
            f"source_id: {yaml_scalar(source_id)}",
            f"routine_date: {routine_date.isoformat()}",
            "---",
        ]
    )
    text = "\n".join(lines) + "\n"

    if body:
        text += "\n" + body.strip("\n") + "\n"

    return text


def wikilink_path(link: str) -> str:
    match = re.match(r"\[\[(.*?)(?:\|.*)?\]\]$", link.strip())

    if not match:
        raise ValueError(f"リンク形式が不正です: {link}")

    path = match.group(1).replace("\\", "/")

    if path.endswith(".md"):
        path = path[:-3]

    return path


def _line_has_link(line: str, path: str) -> bool:
    return re.search(r"\[\[" + re.escape(path) + r"(?:\||\]\])", line) is not None


def _link_exists(lines: list[str], start: int, end: int, path: str) -> bool:
    return any(_line_has_link(lines[index], path) for index in range(start, end))


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def update_task_tree(text: str, project: str, parent_link: str, child_links: list[str]) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    try:
        tree_start = lines.index("## タスクツリー")
    except ValueError as exc:
        raise ValueError("tasks/_タスク.md に ## タスクツリー がありません") from exc

    tree_end = len(lines)

    for index in range(tree_start + 1, len(lines)):
        if lines[index].startswith("## "):
            tree_end = index
            break

    parent_path = wikilink_path(parent_link)
    parent_line = None

    for index in range(tree_start, tree_end):
        if _line_has_link(lines[index], parent_path):
            parent_line = index
            break

    if parent_line is None:
        _insert_new_parent(lines, tree_start, tree_end, project, parent_link, child_links)
    else:
        _insert_missing_children(lines, parent_line, tree_end, child_links)

    return "\n".join(lines)


def _insert_new_parent(lines, tree_start, tree_end, project, parent_link, child_links):
    heading = f"### {project}"
    project_index = None

    for index in range(tree_start + 1, tree_end):
        if lines[index] == heading:
            project_index = index
            break

    block = [f"- {parent_link}"]

    for child in child_links:
        if not _link_exists(lines, tree_start, tree_end, wikilink_path(child)):
            block.append(f"  - {child}")

    if project_index is None:
        prefix = [heading, ""]

        if tree_end == 0 or lines[tree_end - 1] != "":
            prefix = ["", *prefix]

        lines[tree_end:tree_end] = prefix + block + [""]
        return

    section_end = tree_end

    for index in range(project_index + 1, tree_end):
        if lines[index].startswith("### ") or lines[index].startswith("## "):
            section_end = index
            break

    insert_at = section_end

    while insert_at > project_index + 1 and lines[insert_at - 1] == "":
        insert_at -= 1

    addition = block

    if insert_at < len(lines) and lines[insert_at].startswith("#"):
        addition = block + [""]

    lines[insert_at:insert_at] = addition


def _insert_missing_children(lines, parent_line, tree_end, child_links):
    limit = tree_end

    for index in range(parent_line + 1, tree_end):
        if lines[index].startswith("### ") or lines[index].startswith("## "):
            limit = index
            break

    indent = _indent(lines[parent_line])
    insert_at = parent_line + 1

    while insert_at < limit:
        line = lines[insert_at]

        if line.strip() == "":
            nxt = insert_at + 1

            while nxt < limit and lines[nxt].strip() == "":
                nxt += 1

            if nxt >= limit:
                break

            next_line = lines[nxt]

            if next_line.startswith("#") or _indent(next_line) <= indent:
                break

            insert_at = nxt
            continue

        if line.startswith("#") or _indent(line) <= indent:
            break

        insert_at += 1

    missing = []

    for child in child_links:
        path = wikilink_path(child)

        if _link_exists(lines, 0, len(lines), path):
            continue

        missing.append(f"{' ' * (indent + 2)}- {child}")

    if missing:
        lines[insert_at:insert_at] = missing


def _reserve_path(path: Path, key, existing_paths: dict, errors: list[str], label: str):
    if path in existing_paths and existing_paths[path] != key:
        errors.append(f"{label} のファイル名が別のタスクと衝突します: {path.name}")
        return False

    if path.exists():
        errors.append(f"{label} の出力先に別のファイルがあります: {path.name}")
        return False

    existing_paths[path] = key
    return True


def generate(tasks_dir: Path, today: date, dry_run: bool = False) -> GenerateResult:
    routines_dir = tasks_dir / "routines"
    items_dir = tasks_dir / "items"
    routine_dir = items_dir / "routine"
    tree_path = tasks_dir / "_タスク.md"
    result = GenerateResult()

    routines, routine_errors = load_routines(routines_dir)
    result.errors.extend(routine_errors)
    existing, index_errors = index_existing(items_dir)
    result.errors.extend(index_errors)

    if result.errors:
        return result

    writes = []
    tree_groups = []
    reserved_paths = {path: key for key, path in existing.items()}

    for routine in routines:
        if not routine.enabled:
            result.disabled.append(routine.id)
            continue

        for routine_date in iter_occurrences(routine, today):
            date_text = routine_date.isoformat()
            parent_key = (routine.id, date_text)
            parent_existed = parent_key in existing
            parent_path = existing.get(parent_key) or occurrence_path(
                routine_dir,
                routine_date,
                [routine.title],
            )

            if not parent_existed and not _reserve_path(
                parent_path,
                parent_key,
                reserved_paths,
                result.errors,
                routine.title,
            ):
                continue

            child_plans = []

            for child in routine.children:
                source_id = f"{routine.id}/{child.id}"
                child_key = (source_id, date_text)
                child_existed = child_key in existing
                child_path = existing.get(child_key) or occurrence_path(
                    routine_dir,
                    routine_date,
                    [routine.title, child.title],
                )

                if not child_existed and not _reserve_path(
                    child_path,
                    child_key,
                    reserved_paths,
                    result.errors,
                    child.title,
                ):
                    child_plans = None
                    break

                child_plans.append(
                    {
                        "child": child,
                        "path": child_path,
                        "existed": child_existed,
                        "source_id": source_id,
                    }
                )

            if child_plans is None:
                continue

            if result.errors:
                continue

            parent_link = task_link(tasks_dir, parent_path, routine.title)
            child_links = {
                plan["child"].id: task_link(tasks_dir, plan["path"], plan["child"].title)
                for plan in child_plans
            }
            created_any = False

            if parent_existed:
                result.skipped.append(f"{routine.id} {date_text}")
            else:
                writes.append(
                    (
                        parent_path,
                        render_task(
                            title=routine.title,
                            project=routine.project,
                            routine_date=routine_date,
                            priority=routine.priority,
                            estimate=routine.estimate,
                            parent_link="",
                            depends_on=[],
                            source_id=routine.id,
                            body=routine.body,
                        ),
                    )
                )
                result.created.append(parent_path)
                created_any = True

            for plan in child_plans:
                child = plan["child"]

                if plan["existed"]:
                    result.skipped.append(f"{plan['source_id']} {date_text}")
                    continue

                depends_on = [child_links[dep_id] for dep_id in child.depends_on]
                writes.append(
                    (
                        plan["path"],
                        render_task(
                            title=child.title,
                            project=routine.project,
                            routine_date=routine_date,
                            priority=child.priority,
                            estimate=child.estimate,
                            parent_link=parent_link,
                            depends_on=depends_on,
                            source_id=plan["source_id"],
                            body=child.body,
                        ),
                    )
                )
                result.created.append(plan["path"])
                created_any = True

            if created_any:
                tree_groups.append(
                    (
                        routine.project,
                        parent_link,
                        [child_links[child.id] for child in routine.children],
                    )
                )

    if result.errors:
        result.created.clear()
        result.skipped.clear()
        return result

    tree_text = None
    original_tree = None

    if tree_groups:
        if not tree_path.exists():
            result.errors.append("tasks/_タスク.md がありません")
            result.created.clear()
            return result

        original_tree = tree_path.read_text(encoding="utf-8")
        tree_text = original_tree.replace("\r\n", "\n").replace("\r", "\n")

        try:
            for project, parent_link, child_links in tree_groups:
                tree_text = update_task_tree(tree_text, project, parent_link, child_links)
        except ValueError as exc:
            result.errors.append(str(exc))
            result.created.clear()
            return result

    if dry_run:
        return result

    for path, content in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    if tree_text is not None and tree_text != original_tree.replace("\r\n", "\n").replace("\r", "\n"):
        tree_path.write_text(tree_text, encoding="utf-8", newline="\n")

    return result


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def main(argv=None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="ルーティーン定義から期日ごとのタスクを生成する"
    )
    parser.add_argument("--today", help="基準日。YYYY-MM-DD。省略時は本日")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルを書かずに、作成予定だけ表示する",
    )
    args = parser.parse_args(argv)

    if args.today:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print("--today は YYYY-MM-DD で指定してください", file=sys.stderr)
            return 2
    else:
        today = date.today()

    tasks_dir = Path(__file__).resolve().parent.parent
    result = generate(tasks_dir, today, dry_run=args.dry_run)
    verb = "作成予定" if args.dry_run else "作成"

    for error in result.errors:
        print(error, file=sys.stderr)

    for path in result.created:
        print(f"{verb}: {path.relative_to(tasks_dir.parent)}")

    for item in result.skipped:
        print(f"スキップ: {item}")

    for routine_id in result.disabled:
        print(f"無効: {routine_id}")

    print(
        f"created={len(result.created)} skipped={len(result.skipped)} "
        f"disabled={len(result.disabled)} errors={len(result.errors)}"
    )
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
