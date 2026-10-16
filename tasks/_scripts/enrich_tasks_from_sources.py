"""個人タスクの外部ポインタと本文セクションを取得キャッシュから補完する。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

from compare_inbox import as_text, load_json_list, merge_candidates
from task_properties import single_choice
from normalize_task_headings import normalize_inner
from task_source_links import (
    as_str,
    github_pointer_from_url,
    is_routine_task,
    parse_display_github_id,
    task_source_identities,
)

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"
ROUTINES = VAULT / "tasks" / "routines"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SECTION_NAMES = ("概要", "やったこと", "残りのやること")
TERMINAL = frozenset({"done", "canceled"})
REDACTED_URL = re.compile(r"\[REDACTED\]", re.I)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def load_source_cache() -> dict[tuple[str, str], dict]:
    github_items: list = []
    for rel in (
        "sources/github/assigned-issues.json",
        "sources/github/review-requests.json",
        "sources/github/my-prs.json",
    ):
        path = VAULT / rel
        if path.is_file():
            github_items.extend(load_json_list(path))
    backlog_path = VAULT / "sources/backlog/assigned-issues.json"
    backlog_items = load_json_list(backlog_path) if backlog_path.is_file() else []

    merged: dict[tuple[str, str], dict] = {}
    for candidate in merge_candidates(github_items + backlog_items):
        key = (candidate["source_type"], candidate["source_id"])
        merged[key] = candidate
    return merged


def parse_sections(body: str) -> dict[str, str]:
    body = body.replace("\r\n", "\n")
    result = {name: "" for name in SECTION_NAMES}
    legacy_done = ""
    if "## 完了条件" in body:
        m = re.search(r"^## 完了条件\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL | re.MULTILINE)
        legacy_done = m.group(1).strip() if m else ""
    for name in SECTION_NAMES:
        m = re.search(rf"^## {name}\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL | re.MULTILINE)
        if m:
            result[name] = m.group(1).strip()
    result["_legacy_done"] = legacy_done
    return result


def render_body(sections: dict[str, str]) -> str:
    parts = []
    for name in SECTION_NAMES:
        parts.append(f"## {name}\n")
        content = normalize_inner(sections.get(name, "").strip())
        if content:
            parts.append(content)
            parts.append("")
        else:
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def demote_external_markdown(text: str) -> str:
    """Issue 本文など外部 Markdown をセクション内用に正規化する。"""
    if not text.strip():
        return ""
    lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^##\s+(概要|やったこと|残りのやること)\s*$", line):
            continue
        lines.append(line)
    return normalize_inner("\n".join(lines).strip())


def markdown_section(text: str, heading: str) -> str:
    if not text:
        return ""
    for prefix in ("##", "###", "####"):
        pattern = (
            rf"^{prefix}\s+{re.escape(heading)}\s*\n"
            rf"(.*?)(?=\n#{{1,4}}\s+\S|\Z)"
        )
        m = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if m:
            return demote_external_markdown(m.group(1))
    return ""


def external_summary(text: str) -> str:
    for heading in ("概要", "背景", "現状と困りごと", "目的", "現状"):
        section = markdown_section(text, heading)
        if section:
            return section
    return demote_external_markdown(first_paragraph(text))


def first_paragraph(text: str, max_len: int = 1200) -> str:
    text = text.strip()
    if not text:
        return ""
    para = re.split(r"\n\s*\n", text, maxsplit=1)[0].strip()
    if len(para) > max_len:
        para = para[:max_len].rstrip() + "…"
    return para


def remaining_from_external(text: str) -> str:
    for heading in (
        "受け入れ条件",
        "やること",
        "対応内容",
        "対応方針",
        "期待する挙動",
        "期待する挙動・案",
        "タスク",
    ):
        section = markdown_section(text, heading)
        if section:
            return section
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            bullets.append(stripped[2:].strip())
        elif stripped.startswith("- ") and not stripped.startswith("- [x]"):
            bullets.append(stripped[2:].strip())
    if bullets:
        return "\n".join(f"- {b}" for b in bullets[:12])
    return ""


def routine_definition(source_id: str) -> str:
    if not source_id:
        return ""
    for path in ROUTINES.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        m = FM_RE.match(text.replace("\r\n", "\n"))
        if not m:
            continue
        meta = yaml.safe_load(m.group(1)) or {}
        if as_str(meta.get("id")) == source_id:
            return m.group(2)
    return ""


def gh_fetch_updated_at(url: str) -> str:
    if not url:
        return ""
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{_repo_slug(url)}/issues/{_issue_number(url)}", "-q", ".updated_at"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        return as_text(proc.stdout.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return ""


def _repo_slug(url: str) -> str:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/", url, re.I)
    if not m:
        return ""
    return f"{m.group(1)}/{m.group(2)}"


def _issue_number(url: str) -> str:
    m = re.search(r"/(issues|pull)/(\d+)", url, re.I)
    return m.group(2) if m else ""


def sync_github_fields(data: dict, cache: dict[tuple[str, str], dict]) -> bool:
    changed = False
    url = as_str(data.get("github_url"))
    if url and not single_choice(data.get("github_type")):
        parsed = github_pointer_from_url(url)
        if parsed:
            data["github_type"] = [parsed[0]]
            if not as_str(data.get("github_repo")):
                data["github_repo"] = parsed[1]
            if not as_str(data.get("github_id")):
                data["github_id"] = parsed[2]
            changed = True

    gh_id = as_str(data.get("github_id"))
    parsed_id = parse_display_github_id(gh_id)
    if parsed_id and not single_choice(data.get("github_type")):
        data["github_type"] = [parsed_id[0]]
        changed = True

    if not as_str(data.get("github_updated_at")) and gh_id:
        for source_type, source_id in task_source_identities(data):
            item = cache.get((source_type, source_id))
            if item and item.get("source_updated_at"):
                data["github_updated_at"] = item["source_updated_at"]
                changed = True
                break
        if not as_str(data.get("github_updated_at")) and url:
            fetched = gh_fetch_updated_at(url)
            if fetched:
                data["github_updated_at"] = fetched
                changed = True
    return changed


def sync_backlog_fields(data: dict, cache: dict[tuple[str, str], dict]) -> bool:
    changed = False
    backlog_id = as_str(data.get("backlog_id"))
    if not backlog_id:
        return False
    item = cache.get(("backlog_issue", backlog_id))
    if item:
        if not as_str(data.get("backlog_url")) or REDACTED_URL.search(as_str(data.get("backlog_url"))):
            data["backlog_url"] = item.get("source_url") or data.get("backlog_url")
            changed = True
        if not as_str(data.get("backlog_updated_at")) and item.get("source_updated_at"):
            data["backlog_updated_at"] = item["source_updated_at"]
            changed = True
    return changed


def fill_sections(
    data: dict,
    sections: dict[str, str],
    cache: dict[tuple[str, str], dict],
) -> bool:
    changed = False
    status = single_choice(data.get("status"))
    external_text = ""
    for source_type, source_id in task_source_identities(data):
        item = cache.get((source_type, source_id))
        if item:
            external_text = item.get("_link_text") or ""
            break

    if is_routine_task(data) and not any(sections[n] for n in SECTION_NAMES):
        legacy = sections.get("_legacy_done", "")
        if legacy:
            sections["残りのやること"] = legacy
            changed = True
        if not sections["概要"]:
            rid = single_choice(data.get("source_id"))
            def_body = routine_definition(rid)
            intro = first_paragraph(markdown_section(def_body, "完了条件") or def_body)
            if intro:
                sections["概要"] = intro
            else:
                sections["概要"] = as_str(data.get("title"))
            changed = True

    if not sections["概要"] or sections["概要"].strip() in (
        "### 背景",
        "### 現状と困りごと",
    ):
        if external_text:
            summary = external_summary(external_text)
            if summary:
                sections["概要"] = summary
                changed = True
        elif as_str(data.get("title")):
            sections["概要"] = as_str(data.get("title"))
            changed = True

    if status in TERMINAL:
        return changed

    placeholder_remaining = {"### 背景", "### 現状と困りごと"}
    if not sections["残りのやること"] or sections["残りのやること"].strip() in placeholder_remaining:
        remaining = remaining_from_external(external_text) if external_text else ""
        if not remaining and sections.get("_legacy_done"):
            remaining = sections["_legacy_done"]
        if remaining:
            sections["残りのやること"] = demote_external_markdown(remaining)
            changed = True
        elif sections["概要"] and sections["概要"].strip() not in placeholder_remaining:
            sections["残りのやること"] = sections["概要"]
            changed = True

    return changed


def normalize_routine_github(data: dict) -> bool:
    if not is_routine_task(data):
        return False
    before = {k: data.get(k) for k in ("github_type", "github_repo", "github_id", "github_url", "github_updated_at")}
    data["github_type"] = []
    data["github_repo"] = ""
    data["github_id"] = ""
    data["github_url"] = ""
    data["github_updated_at"] = ""
    data["backlog_id"] = ""
    data["backlog_url"] = ""
    data["backlog_updated_at"] = ""
    after = {k: data.get(k) for k in before}
    return before != after


def write_task(path: Path, data: dict, body: str) -> None:
    header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(f"---\n{header}---\n{body}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cache = load_source_cache()
    changed_files: list[str] = []

    for path in sorted(ITEMS.rglob("*.md")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = FM_RE.match(text)
        if not m:
            continue
        data = yaml.safe_load(m.group(1)) or {}
        sections = parse_sections(m.group(2))
        file_changed = False

        if is_routine_task(data):
            file_changed |= normalize_routine_github(data)

        file_changed |= sync_github_fields(data, cache)
        file_changed |= sync_backlog_fields(data, cache)
        file_changed |= fill_sections(data, sections, cache)

        for name in SECTION_NAMES:
            sections[name] = normalize_inner(sections.get(name, ""))

        new_body = render_body(sections)
        old_body = m.group(2)
        if file_changed or new_body != old_body:
            rel = path.relative_to(VAULT).as_posix()
            changed_files.append(rel)
            if not args.dry_run:
                write_task(path, data, new_body)

    for rel in changed_files:
        print(rel)
    print(f"changed: {len(changed_files)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
