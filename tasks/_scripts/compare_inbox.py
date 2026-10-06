"""取得キャッシュと個人タスクを、source_type と source_id で照合する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


GITHUB_FILES = (
    "sources/github/assigned-issues.json",
    "sources/github/my-prs.json",
    "sources/github/review-requests.json",
)
BACKLOG_FILES = ("sources/backlog/assigned-issues.json",)
SOURCE_FILES = {
    "github": GITHUB_FILES,
    "backlog": BACKLOG_FILES,
}
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

    return {
        "source_type": source_type,
        "source_id": source_id,
        "title": title_of(item),
        "source_url": item.get("sourceUrl") or "",
        "source_updated_at": as_text(item.get("sourceUpdatedAt")),
        "external_state": external_state(item),
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


def task_identity(data: dict) -> tuple[str, str] | None:
    source_type = data.get("source_type")
    if not isinstance(source_type, str) or not source_type or source_type == "routine":
        return None

    source_id = data.get("source_id")
    if isinstance(source_id, str) and source_id:
        return source_type, source_id

    source_repo = data.get("source_repo")
    source_number = data.get("source_number")
    if (
        source_type in ("github_issue", "github_pr")
        and isinstance(source_repo, str)
        and source_repo
        and source_number is not None
        and str(source_number).strip()
    ):
        return source_type, f"{source_repo}#{source_number}"

    return None


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

        identity = task_identity(data)
        if identity is None:
            continue

        linked.setdefault(identity, []).append(
            {
                "path": path.relative_to(vault).as_posix(),
                "title": data.get("title") or "",
                "status": data.get("status") or "",
                "source_updated_at": as_text(data.get("source_updated_at")),
            }
        )

    return linked


def cache_newer(cache_updated_at: str, tasks: list[dict]) -> bool | None:
    cache_time = parse_time(cache_updated_at)
    if cache_time is None or not tasks:
        return None

    task_times = [parse_time(task["source_updated_at"]) for task in tasks]
    known = [item for item in task_times if item is not None]
    if not known:
        return None
    return cache_time > min(known)


def compare(vault: Path, sources: list[str]) -> list[dict]:
    items: list[dict] = []
    for source in sources:
        for relative in SOURCE_FILES[source]:
            items.extend(load_json_list(vault / relative))

    candidates = merge_candidates(items)
    tasks = load_tasks(vault)
    result = []

    for candidate in candidates:
        linked = tasks.get((candidate["source_type"], candidate["source_id"]), [])
        result.append(
            {
                **candidate,
                "linked_tasks": linked,
                "cache_newer": cache_newer(candidate["source_updated_at"], linked),
            }
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--sources", default="github,backlog")
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

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
