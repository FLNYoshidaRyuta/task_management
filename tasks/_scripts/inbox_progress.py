"""無人 Inbox 向けに、todo を in_progress にする信号を決定論的に判定する。"""

from __future__ import annotations

import json
from pathlib import Path

from compare_inbox import as_text, load_json_list, parse_time, split_inbox
from fetch_comments import COMMENT_CACHE_FILES, load_comment_cache

GITHUB_VIEWER_FILE = Path("sources/github/viewer.json")
BACKLOG_VIEWER_FILE = Path("sources/backlog/viewer.json")
GITHUB_MY_PRS_FILE = Path("sources/github/my-prs.json")

SIGNAL_OWN_OPEN_PR = "own_open_pr"
SIGNAL_OWN_COMMENT = "own_comment"


def read_json_object(path: Path) -> dict | None:
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return None
    data = json.loads(raw)
    return data if isinstance(data, dict) else None


def load_github_login(vault: Path) -> str | None:
    data = read_json_object(vault / GITHUB_VIEWER_FILE)
    if not data:
        return None
    login = data.get("login")
    return login.strip() if isinstance(login, str) and login.strip() else None


def load_backlog_user_id(vault: Path) -> str | None:
    data = read_json_object(vault / BACKLOG_VIEWER_FILE)
    if not data:
        return None
    user_id = data.get("id")
    if user_id is None:
        return None
    return str(user_id).strip() or None


def closing_issue_id(ref: dict) -> str | None:
    number = ref.get("number")
    repository = ref.get("repository")
    if number is None or not isinstance(repository, dict):
        return None
    owner = repository.get("owner")
    name = repository.get("name")
    if not isinstance(owner, dict) or not isinstance(name, str):
        return None
    login = owner.get("login")
    if not isinstance(login, str) or not login.strip() or not name.strip():
        return None
    return f"{login.strip()}/{name.strip()}#{number}"


def load_own_open_pr_issue_ids(vault: Path) -> set[str]:
    """github_issue の sourceId（owner/repo#番号）の集合。"""
    keys: set[str] = set()
    path = vault / GITHUB_MY_PRS_FILE
    if not path.is_file():
        return keys
    for item in load_json_list(path):
        closing = item.get("closingIssues")
        if isinstance(closing, list):
            for issue_id in closing:
                if isinstance(issue_id, str) and issue_id:
                    keys.add(issue_id)
            continue
        refs = item.get("closingIssuesReferences")
        if isinstance(refs, list):
            for ref in refs:
                if not isinstance(ref, dict):
                    continue
                issue_id = closing_issue_id(ref)
                if issue_id:
                    keys.add(issue_id)
    return keys


def load_comments_index(vault: Path, sources: list[str]) -> dict[tuple[str, str], list[dict]]:
    index: dict[tuple[str, str], list[dict]] = {}
    if "github" in sources:
        path = vault / COMMENT_CACHE_FILES["github"]
        if path.is_file():
            for entry in load_comment_cache(path):
                source_type = entry.get("sourceType")
                source_id = entry.get("sourceId")
                comments = entry.get("comments")
                if (
                    isinstance(source_type, str)
                    and isinstance(source_id, str)
                    and source_type
                    and source_id
                    and isinstance(comments, list)
                ):
                    index[(source_type, source_id)] = comments
    if "backlog" in sources:
        path = vault / COMMENT_CACHE_FILES["backlog"]
        if path.is_file():
            for entry in load_comment_cache(path):
                source_type = entry.get("sourceType")
                source_id = entry.get("sourceId")
                comments = entry.get("comments")
                if (
                    isinstance(source_type, str)
                    and isinstance(source_id, str)
                    and source_type
                    and source_id
                    and isinstance(comments, list)
                ):
                    index[(source_type, source_id)] = comments
    return index


def comment_is_own(comment: dict, source_type: str, github_login: str | None, backlog_user_id: str | None) -> bool:
    if source_type in ("github_issue", "github_pr"):
        if not github_login:
            return False
        author = comment.get("author")
        return isinstance(author, str) and author.strip() == github_login
    if source_type == "backlog_issue":
        if not backlog_user_id:
            return False
        author_id = comment.get("authorId")
        if not isinstance(author_id, str) or not author_id.strip():
            return False
        return author_id.strip() == backlog_user_id
    return False


def has_own_comment_after(
    source_type: str,
    source_id: str,
    task_updated_at: str,
    comments: list[dict] | None,
    github_login: str | None,
    backlog_user_id: str | None,
) -> bool:
    if comments is None:
        return False
    task_time = parse_time(task_updated_at)
    if task_time is None:
        return False
    for comment in comments:
        if not comment_is_own(comment, source_type, github_login, backlog_user_id):
            continue
        created = parse_time(comment.get("createdAt"))
        if created is not None and created > task_time:
            return True
    return False


def signals_for_channel(
    source_type: str,
    source_id: str,
    task_updated_at: str,
    own_pr_issues: set[str],
    comments_index: dict[tuple[str, str], list[dict]],
    github_login: str | None,
    backlog_user_id: str | None,
) -> list[str]:
    reasons: list[str] = []
    if source_type == "github_issue" and source_id in own_pr_issues:
        reasons.append(SIGNAL_OWN_OPEN_PR)
    comments = comments_index.get((source_type, source_id))
    if has_own_comment_after(
        source_type,
        source_id,
        task_updated_at,
        comments,
        github_login,
        backlog_user_id,
    ):
        reasons.append(SIGNAL_OWN_COMMENT)
    return reasons


def task_channel_updated_at(task: dict, source_type: str) -> str:
    return as_text(task.get("source_updated_at"))


def analyze(
    vault: Path,
    sources: list[str],
    compare_result: dict,
) -> dict:
    buckets = split_inbox(compare_result)
    candidates_by_key = {
        (c["source_type"], c["source_id"]): c for c in compare_result.get("candidates", [])
    }

    github_login = load_github_login(vault) if "github" in sources else None
    backlog_user_id = load_backlog_user_id(vault) if "backlog" in sources else None
    own_pr_issues = load_own_open_pr_issue_ids(vault) if "github" in sources else set()
    comments_index = load_comments_index(vault, sources)

    new_status: dict[tuple[str, str], str] = {}
    for item in buckets["new"]:
        key = (item["source_type"], item["source_id"])
        status = "todo"
        if key[0] == "github_issue" and key[1] in own_pr_issues:
            status = "in_progress"
        new_status[key] = status

    updated_keys = {(c["source_type"], c["source_id"]) for c in buckets["updated"]}
    extra_updates: list[dict] = []
    changes_by_path: dict[str, dict] = {}

    for key, candidate in candidates_by_key.items():
        linked = candidate.get("linked_tasks") or []
        if not linked:
            continue
        source_type, source_id = key
        if source_type not in ("github_issue", "backlog_issue"):
            continue

        channel_has_pr_signal = False
        for task in linked:
            if task.get("status") != "todo":
                continue
            task_updated = task_channel_updated_at(task, source_type)
            reasons = signals_for_channel(
                source_type,
                source_id,
                task_updated,
                own_pr_issues,
                comments_index,
                github_login,
                backlog_user_id,
            )
            if not reasons:
                continue
            if SIGNAL_OWN_OPEN_PR in reasons:
                channel_has_pr_signal = True
            path = task.get("path") or ""
            if not path:
                continue
            entry = changes_by_path.get(path)
            if entry is None:
                changes_by_path[path] = {
                    "path": path,
                    "to": "in_progress",
                    "reasons": list(reasons),
                    "sources": [{"source_type": source_type, "source_id": source_id}],
                }
                continue
            for reason in reasons:
                if reason not in entry["reasons"]:
                    entry["reasons"].append(reason)
            entry["sources"].append({"source_type": source_type, "source_id": source_id})

        if (
            key not in updated_keys
            and source_type == "github_issue"
            and channel_has_pr_signal
        ):
            public = {k: v for k, v in candidate.items() if not str(k).startswith("_")}
            extra = {**public, "cache_newer": False, "progress_only": True}
            extra_updates.append(extra)

    merged_updated = list(buckets["updated"])
    for item in extra_updates:
        merged_updated.append(item)

    status_changes = list(changes_by_path.values())

    missing_comment_keys: list[str] = []
    for item in buckets["updated"]:
        key = (item["source_type"], item["source_id"])
        if key not in comments_index:
            missing_comment_keys.append(f"{key[0]}:{key[1]}")

    return {
        "new_status": new_status,
        "updated_candidates": merged_updated,
        "status_changes": status_changes,
        "missing_comment_keys": missing_comment_keys,
        "comments_index": comments_index,
    }


def guard_identity(item: dict, progress_only: bool, in_progress: bool) -> str:
    source_type = str(item.get("source_type") or "").strip()
    source_id = str(item.get("source_id") or "").strip()
    updated = str(item.get("source_updated_at") or "").strip()
    if in_progress and progress_only:
        return f"{source_type}:{source_id}@own_open_pr|in_progress"
    base = f"{source_type}:{source_id}@{updated}"
    if in_progress:
        return f"{base}|in_progress"
    return base


def candidate_needs_in_progress(item: dict, status_changes: list[dict]) -> bool:
    source_type = item.get("source_type")
    source_id = item.get("source_id")
    for change in status_changes:
        for source in change.get("sources") or []:
            if source.get("source_type") == source_type and source.get("source_id") == source_id:
                return True
    return False


def enrich_new_candidates(candidates: list[dict], new_status: dict[tuple[str, str], str]) -> list[dict]:
    enriched: list[dict] = []
    for item in candidates:
        key = (item["source_type"], item["source_id"])
        copy = dict(item)
        copy["status"] = new_status.get(key, "todo")
        enriched.append(copy)
    return enriched


def ensure_comment_cache_for_updates(vault: Path, sources: list[str], compare_result: dict) -> None:
    """cache_newer の候補にコメントキャッシュが無ければ RuntimeError。"""
    analysis = analyze(vault, sources, compare_result)
    missing = analysis["missing_comment_keys"]
    if missing:
        joined = ", ".join(sorted(missing))
        raise RuntimeError(
            f"comment cache missing for cache_newer candidates: {joined}. "
            "Run fetch_comments.py --inbox-updates first."
        )
