"""github_repo の owner/ を除きリポジトリ名だけにする（一回限りの移行）。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from task_source_links import GITHUB_URL_RE, REPO_WITH_OWNER_RE, as_str

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
GITHUB_REPO_LINE_RE = re.compile(r"^(\s*)github_repo:\s*(.+)\s*$")


def migrate_frontmatter(fm_text: str, rel: str) -> tuple[str, str | None]:
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        return fm_text, f"{rel}: frontmatter を読めません: {exc}"

    if not isinstance(data, dict):
        return fm_text, f"{rel}: frontmatter がマッピングではありません"

    gh_repo = as_str(data.get("github_repo"))
    if not gh_repo:
        return fm_text, None

    matched = REPO_WITH_OWNER_RE.fullmatch(gh_repo)
    if not matched:
        return fm_text, None

    repo_name = matched.group(2)
    url = as_str(data.get("github_url"))
    if not url:
        return fm_text, f"{rel}: owner/repo 形式の github_repo があるが github_url がありません"

    url_match = GITHUB_URL_RE.search(url)
    if not url_match:
        return fm_text, f"{rel}: github_url が GitHub Issue/PR の URL ではありません"

    url_owner, url_repo, _, _ = url_match.groups()
    if f"{url_owner}/{url_repo}" != gh_repo:
        return fm_text, f"{rel}: github_repo と github_url のリポジトリが一致しません"

    lines = fm_text.split("\n")
    repo_line_indexes = [
        index for index, line in enumerate(lines) if GITHUB_REPO_LINE_RE.match(line)
    ]
    if len(repo_line_indexes) != 1:
        return fm_text, f"{rel}: github_repo 行が複数あるか見つかりません"

    idx = repo_line_indexes[0]
    indent = GITHUB_REPO_LINE_RE.match(lines[idx]).group(1)
    lines[idx] = f"{indent}github_repo: {repo_name}"
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

    print("GitHub repo name-only migration completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
