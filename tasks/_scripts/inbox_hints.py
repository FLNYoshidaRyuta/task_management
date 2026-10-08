"""Inbox でユーザーが選んだ新規・更新について、一致と更新差分を Markdown で出す。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from compare_inbox import (
    SOURCE_FILES,
    as_text,
    compare,
    external_state,
    load_json_list,
    parse_time,
    read_frontmatter,
    title_of,
)
from task_source_links import task_source_identities

IDENTITY_RE = re.compile(r"^[^:]+:.+$")
GITHUB_ISSUE_URL_RE = re.compile(
    r"https://github\.com/([^/\s]+/[^/\s#]+)/issues/(\d+)",
    re.IGNORECASE,
)
GITHUB_PR_URL_RE = re.compile(
    r"https://github\.com/([^/\s]+/[^/\s#]+)/pull/(\d+)",
    re.IGNORECASE,
)
GITHUB_REF_RE = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)\b")

BODY_EXCERPT_LEN = 500


def parse_identity(spec: str) -> tuple[str, str]:
    text = spec.strip()
    if not IDENTITY_RE.match(text):
        raise ValueError(f"invalid identity: {spec}")
    source_type, source_id = text.split(":", 1)
    source_type = source_type.strip()
    source_id = source_id.strip()
    if not source_type or not source_id:
        raise ValueError(f"invalid identity: {spec}")
    return source_type, source_id


def normalize_title(value: str) -> str:
    text = value.strip()
    text = text.replace("：", ":")
    text = re.sub(r"\s+", "", text)
    return text


def load_cache_index(vault: Path, sources: list[str]) -> dict[tuple[str, str], dict]:
    merged: dict[tuple[str, str], dict] = {}
    for source in sources:
        for relative in SOURCE_FILES[source]:
            for item in load_json_list(vault / relative):
                source_type = item.get("sourceType")
                source_id = item.get("sourceId")
                if not isinstance(source_type, str) or not isinstance(source_id, str):
                    continue
                if not source_type or not source_id:
                    continue
                key = (source_type, source_id)
                current = merged.get(key)
                if current is None:
                    merged[key] = item
                    continue
                current_time = parse_time(current.get("sourceUpdatedAt"))
                new_time = parse_time(item.get("sourceUpdatedAt"))
                if current_time is None or (
                    new_time is not None and new_time > current_time
                ):
                    merged[key] = item
    return merged


def load_all_tasks(vault: Path) -> list[dict]:
    items_dir = vault / "tasks" / "items"
    tasks: list[dict] = []
    if not items_dir.is_dir():
        return tasks

    for path in sorted(items_dir.rglob("*.md")):
        relative = path.relative_to(items_dir)
        if relative.parts and relative.parts[0] == "routine":
            continue

        data = read_frontmatter(path)
        if data is None:
            continue

        identities = task_source_identities(data)
        rel_path = path.relative_to(vault).as_posix()
        title = data.get("title") or ""
        if not identities:
            tasks.append(
                {
                    "path": rel_path,
                    "title": title,
                    "source_type": "",
                    "source_id": "",
                }
            )
            continue
        for source_type, source_id in identities:
            tasks.append(
                {
                    "path": rel_path,
                    "title": title,
                    "source_type": source_type,
                    "source_id": source_id,
                }
            )
    return tasks


def body_of_cache_item(item: dict) -> str:
    for key in ("body", "description"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def github_source_ids_in_text(text: str) -> set[str]:
    found: set[str] = set()
    for pattern in (GITHUB_ISSUE_URL_RE, GITHUB_PR_URL_RE):
        for match in pattern.finditer(text):
            found.add(f"{match.group(1)}#{match.group(2)}")
    for match in GITHUB_REF_RE.finditer(text):
        found.add(f"{match.group(1)}#{match.group(2)}")
    return found


def endpoint_label(source_type: str, source_id: str, title: str, path: str = "") -> str:
    if path:
        return f"`{source_type}` `{source_id}` | task: `{path}` | title: {title}"
    return f"`{source_type}` `{source_id}` | title: {title}"


def pair_key(a: tuple[str, str, str], b: tuple[str, str, str]) -> tuple:
    return tuple(sorted((a, b)))


def collect_matches(
    new_keys: list[tuple[str, str]],
    cache_index: dict[tuple[str, str], dict],
    existing_tasks: list[dict],
) -> list[str]:
    lines: list[str] = []
    seen_pairs: set[tuple] = set()

    new_endpoints: list[dict] = []
    for key in new_keys:
        item = cache_index.get(key)
        title = title_of(item) if item else ""
        new_endpoints.append(
            {
                "source_type": key[0],
                "source_id": key[1],
                "title": title,
                "path": "",
                "body": body_of_cache_item(item) if item else "",
            }
        )

    def add_same_title(left: dict, right: dict) -> None:
        if not left["title"] or not right["title"]:
            return
        if normalize_title(left["title"]) != normalize_title(right["title"]):
            return
        key = pair_key(
            (left["source_type"], left["source_id"], left["path"]),
            (right["source_type"], right["source_id"], right["path"]),
        )
        if key in seen_pairs:
            return
        seen_pairs.add(key)
        lines.append(
            "- `same_title`: "
            f"{endpoint_label(left['source_type'], left['source_id'], left['title'], left['path'])}"
            " ↔ "
            f"{endpoint_label(right['source_type'], right['source_id'], right['title'], right['path'])}"
        )

    def add_github_ref(from_ep: dict, to_source_id: str, to_ep: dict) -> None:
        if not to_source_id or to_source_id not in github_source_ids_in_text(from_ep["body"]):
            return
        key = pair_key(
            (from_ep["source_type"], from_ep["source_id"], from_ep["path"]),
            (to_ep["source_type"], to_ep["source_id"], to_ep["path"]),
        )
        if key in seen_pairs:
            return
        seen_pairs.add(key)
        quote = ""
        for line in from_ep["body"].splitlines():
            if to_source_id in line or to_source_id.split("#")[0] in line:
                quote = line.strip()[:200]
                break
        if not quote:
            quote = from_ep["body"].strip()[:200]
        lines.append(
            "- `github_ref`: "
            f"{endpoint_label(from_ep['source_type'], from_ep['source_id'], from_ep['title'], from_ep['path'])}"
            " → "
            f"`{to_ep['source_type']}` `{to_ep['source_id']}`"
            f" | quote: {quote}"
        )

    for i, left in enumerate(new_endpoints):
        for right in new_endpoints[i + 1 :]:
            add_same_title(left, right)
        for task in existing_tasks:
            right = {
                "source_type": task["source_type"],
                "source_id": task["source_id"],
                "title": task["title"],
                "path": task["path"],
                "body": "",
            }
            add_same_title(left, right)
            if right["source_id"]:
                add_github_ref(left, right["source_id"], right)
            add_github_ref(right, left["source_id"], left)

    for i, left in enumerate(new_endpoints):
        for right in new_endpoints[i + 1 :]:
            if right["source_id"]:
                add_github_ref(left, right["source_id"], right)
            if left["source_id"]:
                add_github_ref(right, left["source_id"], left)

    return lines


def format_update_section(
    update_keys: list[tuple[str, str]],
    candidates_by_key: dict[tuple[str, str], dict],
    cache_index: dict[tuple[str, str], dict],
) -> list[str]:
    lines: list[str] = []
    for key in update_keys:
        candidate = candidates_by_key.get(key)
        if candidate is None:
            continue
        raw = cache_index.get(key, {})
        cache_title = candidate.get("title") or title_of(raw)
        cache_updated = candidate.get("source_updated_at") or ""
        state = candidate.get("external_state") or external_state(raw)
        body = body_of_cache_item(raw)

        for task in candidate.get("linked_tasks") or []:
            lines.append(
                f"- `{key[0]}` `{key[1]}` | task: `{task.get('path') or ''}`"
            )
            lines.append(
                f"  - cache source_updated_at: {cache_updated}"
            )
            lines.append(
                f"  - task source_updated_at: {task.get('source_updated_at') or ''}"
            )
            task_title = task.get("title") or ""
            if task_title and cache_title and normalize_title(task_title) != normalize_title(
                cache_title
            ):
                lines.append(f"  - cache title: {cache_title}")
                lines.append(f"  - task title: {task_title}")
            if state:
                lines.append(f"  - external state: {state}")
            if body:
                excerpt = body.strip()
                if len(excerpt) > BODY_EXCERPT_LEN:
                    excerpt = excerpt[:BODY_EXCERPT_LEN] + "…"
                lines.append(f"  - cache body excerpt: {excerpt}")
    return lines


def build_hints(
    vault: Path,
    sources: list[str],
    new_keys: list[tuple[str, str]],
    update_keys: list[tuple[str, str]],
) -> str:
    result = compare(vault, sources)
    candidates_by_key = {
        (c["source_type"], c["source_id"]): c for c in result.get("candidates", [])
    }

    for key in new_keys:
        if key not in candidates_by_key:
            raise ValueError(f"unknown new candidate: {key[0]}:{key[1]}")

    for key in update_keys:
        candidate = candidates_by_key.get(key)
        if candidate is None:
            raise ValueError(f"unknown update candidate: {key[0]}:{key[1]}")

    cache_index = load_cache_index(vault, sources)
    existing_tasks = load_all_tasks(vault)

    lines: list[str] = []
    lines.append("## 一致")
    if new_keys:
        match_lines = collect_matches(new_keys, cache_index, existing_tasks)
        if match_lines:
            lines.extend(match_lines)
        else:
            lines.append("（一致なし）")
    else:
        lines.append("（0件）")
    lines.append("")

    lines.append("## 更新差分")
    if update_keys:
        update_lines = format_update_section(update_keys, candidates_by_key, cache_index)
        if update_lines:
            lines.extend(update_lines)
        else:
            lines.append("（0件）")
    else:
        lines.append("（0件）")
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
        "--new",
        action="append",
        default=[],
        metavar="TYPE:ID",
        help="selected new candidate (repeatable)",
    )
    parser.add_argument(
        "--update",
        action="append",
        default=[],
        metavar="TYPE:ID",
        help="selected update candidate (repeatable)",
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
        new_keys = [parse_identity(item) for item in args.new]
        update_keys = [parse_identity(item) for item in args.update]
        text = build_hints(vault, sources, new_keys, update_keys)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc

    configure_stdout_utf8()
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
