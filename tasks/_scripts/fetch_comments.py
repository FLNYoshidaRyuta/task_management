"""Inbox の更新対象について、会話コメントだけを別キャッシュへ取得する。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from compare_inbox import as_text, parse_time

IDENTITY_RE = re.compile(r"^[^:]+:.+$")
GITHUB_SOURCE_TYPES = frozenset({"github_issue", "github_pr"})
BACKLOG_SOURCE_TYPES = frozenset({"backlog_issue"})
GITHUB_ID_RE = re.compile(r"^([^#]+)#(\d+)$")
BACKLOG_KEY_RE = re.compile(r"^[A-Z0-9_]+-\d+$")

COMMENT_CACHE_FILES = {
    "github": "sources/github/comments.json",
    "backlog": "sources/backlog/comments.json",
}


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


def load_env_file(env_path: Path) -> None:
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if "=" not in text:
            continue
        name, value = text.split("=", 1)
        name = name.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if name:
            import os

            os.environ[name] = value


def parse_github_source_id(source_id: str) -> tuple[str, str]:
    matched = GITHUB_ID_RE.match(source_id.strip())
    if not matched:
        raise ValueError(f"invalid github source_id: {source_id}")
    return matched.group(1), matched.group(2)


def sort_comments(comments: list[dict]) -> list[dict]:
    def sort_key(item: dict) -> tuple:
        parsed = parse_time(item.get("createdAt"))
        if parsed is None:
            return (1, "")
        return (0, parsed.isoformat())

    return sorted(comments, key=sort_key)


def normalize_github_comment(item: dict) -> dict:
    user = item.get("user")
    author = ""
    if isinstance(user, dict):
        login = user.get("login")
        author = login if isinstance(login, str) else ""
    return {
        "id": str(item.get("id", "")),
        "author": author,
        "createdAt": as_text(item.get("created_at")),
        "updatedAt": as_text(item.get("updated_at")),
        "url": item.get("html_url") if isinstance(item.get("html_url"), str) else "",
        "body": item.get("body") if isinstance(item.get("body"), str) else "",
    }


def normalize_backlog_comment(item: dict, base_url: str, issue_key: str) -> dict:
    created_user = item.get("createdUser")
    author = ""
    if isinstance(created_user, dict):
        name = created_user.get("name")
        author = name if isinstance(name, str) else ""
    comment_id = item.get("id")
    url = ""
    if comment_id is not None:
        url = f"{base_url.rstrip('/')}/view/{issue_key}#comment-{comment_id}"
    content = item.get("content")
    return {
        "id": str(comment_id if comment_id is not None else ""),
        "author": author,
        "createdAt": as_text(item.get("created")),
        "updatedAt": as_text(item.get("updated")),
        "url": url,
        "body": content if isinstance(content, str) else "",
    }


def load_comment_cache(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"comment cache is not a list: {path}")
    return data


def save_comment_cache(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def merge_comment_entries(
    existing: list[dict],
    updates: list[tuple[str, str, list[dict]]],
) -> list[dict]:
    index: dict[tuple[str, str], dict] = {}
    for entry in existing:
        source_type = entry.get("sourceType")
        source_id = entry.get("sourceId")
        if not isinstance(source_type, str) or not isinstance(source_id, str):
            continue
        if not source_type or not source_id:
            continue
        index[(source_type, source_id)] = entry

    for source_type, source_id, comments in updates:
        index[(source_type, source_id)] = {
            "sourceType": source_type,
            "sourceId": source_id,
            "comments": comments,
        }

    return sorted(
        index.values(),
        key=lambda item: (str(item.get("sourceType", "")), str(item.get("sourceId", ""))),
    )


def fetch_github_comments_api(source_type: str, source_id: str) -> list[dict]:
    if source_type not in GITHUB_SOURCE_TYPES:
        raise ValueError(f"unsupported github source_type: {source_type}")
    owner_repo, number = parse_github_source_id(source_id)
    command = ["gh", "api", f"repos/{owner_repo}/issues/{number}/comments"]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"gh api failed for {source_id}: {message}")

    raw = completed.stdout.strip()
    items = json.loads(raw) if raw else []
    if not isinstance(items, list):
        raise RuntimeError(f"unexpected gh api response for {source_id}")

    normalized = [normalize_github_comment(item) for item in items if isinstance(item, dict)]
    return sort_comments(normalized)


def backlog_get_json(base_url: str, api_key: str, path: str) -> object:
    query = urllib.parse.urlencode({"apiKey": api_key})
    url = f"{base_url.rstrip('/')}{path}?{query}"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"backlog api failed: {path} ({exc.code}) {body}") from exc
    return json.loads(payload)


def fetch_backlog_comments_api(
    source_id: str,
    base_url: str,
    api_key: str,
) -> list[dict]:
    if not BACKLOG_KEY_RE.match(source_id):
        raise ValueError(f"invalid backlog source_id: {source_id}")
    items = backlog_get_json(base_url, api_key, f"/api/v2/issues/{source_id}/comments")
    if not isinstance(items, list):
        raise RuntimeError(f"unexpected backlog api response for {source_id}")
    normalized = [
        normalize_backlog_comment(item, base_url, source_id)
        for item in items
        if isinstance(item, dict)
    ]
    return sort_comments(normalized)


def fetch_updates(
    vault: Path,
    sources: list[str],
    update_keys: list[tuple[str, str]],
    github_fetcher: Callable[[str, str], list[dict]] | None = None,
    backlog_fetcher: Callable[[str], list[dict]] | None = None,
) -> None:
    github_fetch = github_fetcher or fetch_github_comments_api
    backlog_fetch = backlog_fetcher

    env_path = vault / ".env"
    load_env_file(env_path)

    backlog_base_url = ""
    backlog_api_key = ""
    if "backlog" in sources:
        import os

        backlog_base_url = os.environ.get("BACKLOG_BASE_URL", "").strip()
        backlog_api_key = os.environ.get("BACKLOG_API_KEY", "").strip()
        if backlog_fetch is None:
            if not backlog_base_url or not backlog_api_key:
                raise RuntimeError(
                    "BACKLOG_BASE_URL and BACKLOG_API_KEY are required for backlog comments"
                )
            backlog_fetch = lambda issue_key: fetch_backlog_comments_api(
                issue_key, backlog_base_url, backlog_api_key
            )

    github_updates: list[tuple[str, str, list[dict]]] = []
    backlog_updates: list[tuple[str, str, list[dict]]] = []

    for source_type, source_id in update_keys:
        if source_type in GITHUB_SOURCE_TYPES:
            if "github" not in sources:
                raise ValueError(f"github not in sources: {source_type}:{source_id}")
            comments = github_fetch(source_type, source_id)
            github_updates.append((source_type, source_id, comments))
            continue
        if source_type in BACKLOG_SOURCE_TYPES:
            if "backlog" not in sources:
                raise ValueError(f"backlog not in sources: {source_type}:{source_id}")
            if backlog_fetch is None:
                raise RuntimeError("backlog fetcher is not configured")
            comments = backlog_fetch(source_id)
            backlog_updates.append((source_type, source_id, comments))
            continue
        raise ValueError(f"unsupported source_type for comments: {source_type}")

    if github_updates and "github" in sources:
        path = vault / COMMENT_CACHE_FILES["github"]
        merged = merge_comment_entries(load_comment_cache(path), github_updates)
        save_comment_cache(path, merged)

    if backlog_updates and "backlog" in sources:
        path = vault / COMMENT_CACHE_FILES["backlog"]
        merged = merge_comment_entries(load_comment_cache(path), backlog_updates)
        save_comment_cache(path, merged)


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--sources", default="github,backlog")
    parser.add_argument(
        "--update",
        action="append",
        default=[],
        metavar="TYPE:ID",
        help="update target (repeatable)",
    )
    args = parser.parse_args()

    vault = args.vault or Path(__file__).resolve().parents[2]
    sources = [item.strip() for item in args.sources.split(",") if item.strip()]
    if not sources:
        raise SystemExit("sources is empty")
    if not args.update:
        raise SystemExit("at least one --update is required")

    try:
        update_keys = [parse_identity(item) for item in args.update]
        fetch_updates(vault, sources, update_keys)
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    configure_stdout_utf8()
    sys.stdout.write("Comment cache updated.\n")


if __name__ == "__main__":
    main()
