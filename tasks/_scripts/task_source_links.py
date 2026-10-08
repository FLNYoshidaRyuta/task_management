"""個人タスク frontmatter の GitHub / Backlog ポインタを読む。"""

from __future__ import annotations

import re

from task_properties import single_choice

LEGACY_SOURCE_TYPES = frozenset({"github_issue", "github_pr", "backlog_issue"})

GITHUB_URL_RE = re.compile(
    r"https://github\.com/([^/\s]+)/([^/\s]+)/(issues|pull)/(\d+)",
    re.IGNORECASE,
)
BACKLOG_KEY_RE = re.compile(r"MYPL-\d+")


def as_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def is_routine_task(data: dict) -> bool:
    return single_choice(data.get("source_type")) == "routine"


def legacy_identity(data: dict) -> tuple[str, str] | None:
    source_type = single_choice(data.get("source_type"))
    if source_type not in LEGACY_SOURCE_TYPES:
        return None

    source_id = as_str(data.get("source_id"))
    if source_id:
        return source_type, source_id

    source_repo = as_str(data.get("source_repo"))
    source_number = data.get("source_number")
    if (
        source_type in ("github_issue", "github_pr")
        and source_repo
        and source_number is not None
        and str(source_number).strip()
    ):
        return source_type, f"{source_repo}#{source_number}"

    return None


def task_source_identities(data: dict) -> list[tuple[str, str]]:
    if is_routine_task(data):
        return []

    identities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    github_type = single_choice(data.get("github_type"))
    github_id = as_str(data.get("github_id"))
    if github_type and github_id:
        key = (github_type, github_id)
        if key not in seen:
            identities.append(key)
            seen.add(key)

    backlog_id = as_str(data.get("backlog_id"))
    if backlog_id:
        key = ("backlog_issue", backlog_id)
        if key not in seen:
            identities.append(key)
            seen.add(key)

    return identities


def task_url_for_channel(data: dict, source_type: str) -> str:
    if source_type in ("github_issue", "github_pr"):
        url = as_str(data.get("github_url"))
        if url:
            return url
        if single_choice(data.get("source_type")) in ("github_issue", "github_pr"):
            return as_str(data.get("source_url"))
    if source_type == "backlog_issue":
        url = as_str(data.get("backlog_url"))
        if url:
            return url
        if single_choice(data.get("source_type")) == "backlog_issue":
            return as_str(data.get("source_url"))
    return ""


def task_updated_at_for_channel(data: dict, source_type: str) -> str:
    if source_type in ("github_issue", "github_pr"):
        updated = as_str(data.get("github_updated_at"))
        if updated:
            return updated
        if single_choice(data.get("source_type")) in ("github_issue", "github_pr"):
            return as_str(data.get("source_updated_at"))
    if source_type == "backlog_issue":
        updated = as_str(data.get("backlog_updated_at"))
        if updated:
            return updated
        if single_choice(data.get("source_type")) == "backlog_issue":
            return as_str(data.get("source_updated_at"))
    return ""


def github_id_from_url(url: str) -> tuple[str, str] | None:
    matched = GITHUB_URL_RE.search(url)
    if not matched:
        return None
    owner, repo, kind, number = matched.groups()
    name = f"{owner}/{repo}"
    source_type = "github_pr" if kind.lower() == "pull" else "github_issue"
    return source_type, f"{name}#{number}"


def backlog_keys_from_text(text: str) -> list[str]:
    if not text:
        return []
    return list(dict.fromkeys(BACKLOG_KEY_RE.findall(text)))


def github_ids_from_text(text: str) -> list[tuple[str, str]]:
    if not text:
        return []
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for matched in GITHUB_URL_RE.finditer(text):
        owner, repo, kind, number = matched.groups()
        source_type = "github_pr" if kind.lower() == "pull" else "github_issue"
        key = (source_type, f"{owner}/{repo}#{number}")
        if key not in seen:
            found.append(key)
            seen.add(key)
    return found


def uses_legacy_source_fields(data: dict) -> bool:
    if legacy_identity(data) is not None:
        return True
    source_type = single_choice(data.get("source_type"))
    return source_type in LEGACY_SOURCE_TYPES and bool(as_str(data.get("source_id")))


def uses_new_source_fields(data: dict) -> bool:
    if single_choice(data.get("github_type")) and as_str(data.get("github_id")):
        return True
    return bool(as_str(data.get("backlog_id")))
