"""github_id を github_repo と Issue# / PR# に分割する（一回限りの移行）。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from task_properties import single_choice
from task_source_links import (
    REPO_WITH_OWNER_RE,
    display_github_id,
    github_id_from_url,
    parse_display_github_id,
    parse_legacy_github_id,
)

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
GITHUB_ID_LINE_RE = re.compile(r"^github_id:\s*(.+)\s*$")


def migrate_frontmatter(fm_text: str, rel: str) -> tuple[str, str | None]:
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        return fm_text, f"{rel}: frontmatter を読めません: {exc}"

    if not isinstance(data, dict):
        return fm_text, f"{rel}: frontmatter がマッピングではありません"

    raw_id = data.get("github_id")
    if raw_id is None or raw_id == "":
        return fm_text, None

    gh_id = str(raw_id).strip()
    if parse_display_github_id(gh_id):
        return fm_text, None

    legacy = parse_legacy_github_id(gh_id)
    if legacy is None:
        return fm_text, f"{rel}: github_id の形式が不明です: {gh_id}"

    repo_full, number = legacy
    repo_name_match = REPO_WITH_OWNER_RE.fullmatch(repo_full)
    repo_name = repo_name_match.group(2) if repo_name_match else repo_full
    gh_type = single_choice(data.get("github_type"))
    if not gh_type:
        return fm_text, f"{rel}: 旧 github_id があるが github_type がありません"

    url = (data.get("github_url") or "").strip()
    if not url:
        return fm_text, f"{rel}: github_url がありません"

    from_url = github_id_from_url(url)
    if from_url is None:
        return fm_text, f"{rel}: github_url が GitHub Issue/PR の URL ではありません"

    expected_id = f"{repo_full}#{number}"
    if from_url != (gh_type, expected_id):
        return fm_text, f"{rel}: github_url が github_id / github_type と一致しません"

    new_id = display_github_id(gh_type, number)
    lines = fm_text.split("\n")
    id_line_indexes = [
        index
        for index, line in enumerate(lines)
        if GITHUB_ID_LINE_RE.match(line) and parse_legacy_github_id(GITHUB_ID_LINE_RE.match(line).group(1).strip())
    ]
    if len(id_line_indexes) != 1:
        return fm_text, f"{rel}: github_id 行が複数あるか見つかりません"

    idx = id_line_indexes[0]
    if any(line.startswith("github_repo:") for line in lines):
        return fm_text, f"{rel}: github_repo が既にあります"

    indent = re.match(r"^(\s*)", lines[idx]).group(1)
    lines[idx : idx + 1] = [
        f"{indent}github_repo: {repo_name}",
        f"{indent}github_id: {new_id}",
    ]
    return "\n".join(lines), None


def migrate_text(text: str, rel: str = "sample.md") -> tuple[str, str | None]:
    normalized = text.replace("\r\n", "\n")
    match = FM_RE.match(normalized)
    if not match:
        return text, f"{rel}: frontmatter がありません"

    new_fm, error = migrate_frontmatter(match.group(1), rel)
    if error:
        return text, error
    if new_fm == match.group(1):
        return text, None

    return f"---\n{new_fm}\n---\n{match.group(2)}", None


def migrate_file(path: Path) -> str | None:
    rel = path.relative_to(VAULT).as_posix()
    text = path.read_text(encoding="utf-8")
    new_text, error = migrate_text(text, rel)
    if error:
        return error
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    errors: list[str] = []
    for path in sorted(ITEMS.rglob("*.md")):
        message = migrate_file(path)
        if message:
            errors.append(message)

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1

    print("GitHub id split migration completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
