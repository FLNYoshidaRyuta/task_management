"""取得キャッシュと個人タスクを、source_type と source_id で照合する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from task_properties import single_choice
from task_source_links import (
    backlog_keys_from_text,
    github_ids_from_text,
    task_source_identities,
    task_updated_at_for_channel,
    task_url_for_channel,
)


GITHUB_FILES = (
    "sources/github/assigned-issues.json",
    "sources/github/review-requests.json",
)
# 作者が自分の PR。新規・更新・追記の候補にはしない。
# 開いている間は、紐づくタスクをキャッシュ欠落として出さない。
GITHUB_OWN_PR_FILE = "sources/github/my-prs.json"
BACKLOG_FILES = ("sources/backlog/assigned-issues.json",)
SOURCE_FILES = {
    "github": GITHUB_FILES,
    "backlog": BACKLOG_FILES,
}
SOURCE_TYPES_FOR = {
    "github": frozenset({"github_issue", "github_pr"}),
    "backlog": frozenset({"backlog_issue"}),
}
TERMINAL_STATUSES = frozenset({"done", "canceled"})
DATE_MS = re.compile(r"/Date\((-?\d+)(?:[+-]\d+)?\)/")


def parse_time(value) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        matched = DATE_MS.search(text)
        if matched:
            millis = int(matched.group(1))
            return datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def as_text(value) -> str:
    parsed = parse_time(value)
    if parsed is not None:
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    if value is None:
        return ""
    return str(value).strip()


def read_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---\n"):
        return None

    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"frontmatter が閉じていません: {path}")

    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"frontmatter を読めません: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"frontmatter がオブジェクトではありません: {path}")
    return data


def load_json_list(path: Path) -> list:
    if not path.is_file():
        raise FileNotFoundError(f"missing cache: {path}")

    raw = path.read_text(encoding="utf-8-sig").strip()
    items = json.loads(raw) if raw else []
    if isinstance(items, dict):
        return [items]
    if not isinstance(items, list):
        raise ValueError(f"cache is not a list: {path}")
    return items


def external_state(item: dict) -> str:
    state = item.get("state")
    if isinstance(state, str) and state:
        return state

    status = item.get("status")
    if isinstance(status, dict):
        name = status.get("name")
        return name if isinstance(name, str) else ""
    if isinstance(status, str):
        return status
    return ""


def title_of(item: dict) -> str:
    title = item.get("title")
    if isinstance(title, str) and title:
        return title
    summary = item.get("summary")
    return summary if isinstance(summary, str) else ""


def candidate_from_item(item: dict) -> dict | None:
    source_type = item.get("sourceType")
    source_id = item.get("sourceId")
    if not isinstance(source_type, str) or not isinstance(source_id, str):
        return None
    if not source_type or not source_id:
        return None

    link_text = ""
    if source_type == "backlog_issue":
        description = item.get("description")
        link_text = description if isinstance(description, str) else ""
    elif source_type in ("github_issue", "github_pr"):
        body = item.get("body")
        link_text = body if isinstance(body, str) else ""

    return {
        "source_type": source_type,
        "source_id": source_id,
        "title": title_of(item),
        "source_url": item.get("sourceUrl") or "",
        "source_updated_at": as_text(item.get("sourceUpdatedAt")),
        "external_state": external_state(item),
        "_link_text": link_text,
    }


def merge_candidates(items: list[dict]) -> list[dict]:
    merged: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []

    for item in items:
        candidate = candidate_from_item(item)
        if candidate is None:
            continue
        key = (candidate["source_type"], candidate["source_id"])
        current = merged.get(key)
        if current is None:
            merged[key] = candidate
            order.append(key)
            continue

        current_time = parse_time(current["source_updated_at"])
        new_time = parse_time(candidate["source_updated_at"])
        if current_time is None or (new_time is not None and new_time > current_time):
            merged[key] = candidate

    return [merged[key] for key in order]


def load_tasks(vault: Path) -> dict[tuple[str, str], list[dict]]:
    items_dir = vault / "tasks" / "items"
    linked: dict[tuple[str, str], list[dict]] = {}
    if not items_dir.is_dir():
        return linked

    for path in sorted(items_dir.rglob("*.md")):
        relative = path.relative_to(items_dir)
        if relative.parts and relative.parts[0] == "routine":
            continue

        data = read_frontmatter(path)
        if data is None:
            continue

        for source_type, source_id in task_source_identities(data):
            linked.setdefault((source_type, source_id), []).append(
                {
                    "path": path.relative_to(vault).as_posix(),
                    "title": data.get("title") or "",
                    "status": single_choice(data.get("status")),
                    "source_url": task_url_for_channel(data, source_type),
                    "source_updated_at": as_text(
                        task_updated_at_for_channel(data, source_type)
                    ),
                }
            )

    return linked


def find_attach_target(
    candidate: dict,
    tasks: dict[tuple[str, str], list[dict]],
) -> str | None:
    link_text = candidate.get("_link_text") or ""
    source_type = candidate["source_type"]
    source_id = candidate["source_id"]

    if source_type == "backlog_issue":
        for gh_type, gh_id in github_ids_from_text(link_text):
            linked = tasks.get((gh_type, gh_id), [])
            if len(linked) != 1:
                continue
            task = linked[0]
            backlog_linked = tasks.get(("backlog_issue", source_id), [])
            if any(item["path"] == task["path"] for item in backlog_linked):
                continue
            return task["path"]
        return None

    if source_type in ("github_issue", "github_pr"):
        for backlog_key in backlog_keys_from_text(link_text):
            linked = tasks.get(("backlog_issue", backlog_key), [])
            if len(linked) != 1:
                continue
            task = linked[0]
            gh_linked = tasks.get((source_type, source_id), [])
            if any(item["path"] == task["path"] for item in gh_linked):
                continue
            return task["path"]
        return None

    return None


def active_source_types(sources: list[str]) -> frozenset[str]:
    merged: set[str] = set()
    for source in sources:
        merged.update(SOURCE_TYPES_FOR[source])
    return frozenset(merged)


def missing_from_cache(
    vault: Path,
    cache_keys: set[tuple[str, str]],
    source_types: frozenset[str],
) -> list[dict]:
    items_dir = vault / "tasks" / "items"
    grouped: dict[tuple[str, str], list[dict]] = {}
    if not items_dir.is_dir():
        return []

    for path in sorted(items_dir.rglob("*.md")):
        relative = path.relative_to(items_dir)
        if relative.parts and relative.parts[0] == "routine":
            continue

        data = read_frontmatter(path)
        if data is None:
            continue

        status = single_choice(data.get("status"))
        if status in TERMINAL_STATUSES:
            continue

        for source_type, source_id in task_source_identities(data):
            if source_type not in source_types:
                continue
            identity = (source_type, source_id)
            if identity in cache_keys:
                continue

            grouped.setdefault(identity, []).append(
                {
                    "path": path.relative_to(vault).as_posix(),
                    "title": data.get("title") or "",
                    "status": status,
                    "source_url": task_url_for_channel(data, source_type),
                    "source_updated_at": as_text(
                        task_updated_at_for_channel(data, source_type)
                    ),
                }
            )

    return [
        {
            "source_type": key[0],
            "source_id": key[1],
            "tasks": grouped[key],
        }
        for key in sorted(grouped)
    ]


def cache_newer(cache_updated_at: str, tasks: list[dict]) -> bool | None:
    cache_time = parse_time(cache_updated_at)
    if cache_time is None or not tasks:
        return None

    task_times = [parse_time(task["source_updated_at"]) for task in tasks]
    known = [item for item in task_times if item is not None]
    if not known:
        return None
    return cache_time > min(known)


def own_pr_identities(vault: Path, sources: list[str]) -> set[tuple[str, str]]:
    """自分が作者の PR。候補にはせず、欠落判定の在籍だけに使う。"""
    if "github" not in sources:
        return set()

    keys: set[tuple[str, str]] = set()
    for item in load_json_list(vault / GITHUB_OWN_PR_FILE):
        candidate = candidate_from_item(item)
        if candidate is None or candidate["source_type"] != "github_pr":
            continue
        keys.add((candidate["source_type"], candidate["source_id"]))
    return keys


def compare(vault: Path, sources: list[str]) -> dict:
    from skip_inbox import load_skipped_keys

    items: list[dict] = []
    for source in sources:
        for relative in SOURCE_FILES[source]:
            items.extend(load_json_list(vault / relative))

    candidates = merge_candidates(items)
    cache_keys = {(item["source_type"], item["source_id"]) for item in candidates}
    cache_keys.update(own_pr_identities(vault, sources))
    tasks = load_tasks(vault)
    skipped_keys = load_skipped_keys(vault)
    result = []

    for candidate in candidates:
        linked = tasks.get((candidate["source_type"], candidate["source_id"]), [])
        attach_to = None
        if not linked:
            attach_to = find_attach_target(candidate, tasks)

        public = {key: value for key, value in candidate.items() if not key.startswith("_")}
        identity = (candidate["source_type"], candidate["source_id"])
        entry = {
            **public,
            "linked_tasks": linked,
            "cache_newer": cache_newer(candidate["source_updated_at"], linked),
            "skipped": (not linked) and identity in skipped_keys,
        }
        if attach_to:
            entry["attach_to"] = attach_to
        result.append(entry)

    missing = missing_from_cache(vault, cache_keys, active_source_types(sources))

    return {
        "candidates": result,
        "missing_from_cache": missing,
    }


def split_inbox(result: dict) -> dict:
    """新規、追記、更新、キャッシュ欠落を Markdown と同じ条件で分ける。"""
    candidates = result.get("candidates", [])
    missing = result.get("missing_from_cache", [])
    return {
        "new": [
            c
            for c in candidates
            if not c.get("linked_tasks")
            and not c.get("attach_to")
            and not c.get("skipped")
        ],
        "attach": [
            c
            for c in candidates
            if not c.get("linked_tasks")
            and c.get("attach_to")
            and not c.get("skipped")
        ],
        "updated": [
            c
            for c in candidates
            if c.get("linked_tasks") and c.get("cache_newer") is True
        ],
        "missing_from_cache": missing,
        "skipped_hidden": sum(
            1
            for c in candidates
            if c.get("skipped") and not c.get("linked_tasks")
        ),
    }


def format_markdown(result: dict) -> str:
    lines: list[str] = []
    buckets = split_inbox(result)
    new_items = buckets["new"]
    attach_items = buckets["attach"]
    updated_items = buckets["updated"]
    missing = buckets["missing_from_cache"]
    skipped_hidden = buckets["skipped_hidden"]

    lines.append("## 新規候補")
    if not new_items:
        lines.append("（0件）")
    else:
        for i, c in enumerate(new_items, 1):
            lines.append(f"{i}. **{c.get('source_type')}** | `{c.get('source_id')}`")
            lines.append(f"   - title: {c.get('title') or ''}")
            lines.append(f"   - url: {c.get('source_url') or ''}")
            lines.append(
                f"   - state: {c.get('external_state') or ''} | updated: {c.get('source_updated_at') or ''}"
            )
    lines.append("")

    lines.append("## 追記候補")
    if not attach_items:
        lines.append("（0件）")
    else:
        for i, c in enumerate(attach_items, 1):
            lines.append(f"A{i}. **{c.get('source_type')}** | `{c.get('source_id')}`")
            lines.append(f"   - title: {c.get('title') or ''}")
            lines.append(f"   - url: {c.get('source_url') or ''}")
            lines.append(f"   - attach_to: `{c.get('attach_to') or ''}`")
    lines.append("")

    lines.append("## 更新あり")
    if not updated_items:
        lines.append("（0件）")
    else:
        for i, c in enumerate(updated_items, 1):
            lines.append(f"U{i}. **{c.get('source_type')}** | `{c.get('source_id')}`")
            lines.append(f"   - title: {c.get('title') or ''}")
            lines.append(f"   - url: {c.get('source_url') or ''}")
            lines.append(f"   - cache updated: {c.get('source_updated_at') or ''}")
            for t in c.get("linked_tasks") or []:
                lines.append(
                    f"   - task: `{t.get('path') or ''}` | status: {t.get('status') or ''} | task updated: {t.get('source_updated_at') or ''}"
                )
    lines.append("")

    lines.append("## キャッシュに無い未完了タスク")
    if not missing:
        lines.append("（0件）")
    else:
        for i, m in enumerate(missing, 1):
            lines.append(f"M{i}. **{m.get('source_type')}** | `{m.get('source_id')}`")
            for t in m.get("tasks") or []:
                lines.append(f"   - `{t.get('path') or ''}` | {t.get('title') or ''} | status: {t.get('status') or ''} | task updated: {t.get('source_updated_at') or ''}")
                if t.get("source_url"):
                    lines.append(f"     - url: {t.get('source_url')}")
    lines.append("")

    if skipped_hidden > 0:
        lines.append(
            f"タスク化しないとして保持し、今回の提案から外した件数: {skipped_hidden}"
        )
        lines.append("")

    return "\n".join(lines)


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--sources", default="github,backlog")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="output format (default: json)",
    )
    args = parser.parse_args()

    vault = args.vault or Path(__file__).resolve().parents[2]
    sources = [item.strip() for item in args.sources.split(",") if item.strip()]
    unknown = [item for item in sources if item not in SOURCE_FILES]
    if unknown:
        raise SystemExit(f"unsupported source: {', '.join(unknown)}")
    if not sources:
        raise SystemExit("sources is empty")

    try:
        result = compare(vault, sources)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    configure_stdout_utf8()
    if args.format == "markdown":
        text = format_markdown(result)
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
