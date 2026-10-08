"""旧 source_* を github_* / backlog_* に移し、二重管理4組を統合する（一回限りの移行）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from task_properties import single_choice

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"

MERGE_LOSERS = {
    10: 11,
    73: 68,
    71: 69,
    72: 70,
}

LOSER_PATHS = [
    ITEMS / "改善要望" / "ニュース投稿画面の「この画像をGoogleマップの投稿に使用する」という文言を修正.md",
    ITEMS
    / "まいぷれくん"
    / "まいぷれくん： Gemini が遅いと約120秒待って「Request timed out.」で失敗する（本番で OpenRouter への退避が動いていない）.md",
    ITEMS
    / "開発標準化"
    / "dev の Rundeck・cron に手動登録されたジョブを棚卸しし、yaml 管理に一本化する.md",
    ITEMS / "開発標準化" / "dev への DB コピー時に GBP の連携情報も消す.md",
]

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def read_doc(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FM_RE.match(text)
    if not match:
        raise ValueError(f"no frontmatter: {path}")
    data = yaml.safe_load(match.group(1)) or {}
    return data, match.group(2)


def write_doc(path: Path, data: dict, body: str) -> None:
    header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(f"---\n{header}---\n{body}", encoding="utf-8")


def empty_github(data: dict) -> None:
    data["github_type"] = []
    data["github_id"] = ""
    data["github_url"] = ""
    data["github_updated_at"] = ""


def empty_backlog(data: dict) -> None:
    data["backlog_id"] = ""
    data["backlog_url"] = ""
    data["backlog_updated_at"] = ""


def apply_legacy_github(data: dict) -> None:
    source_type = single_choice(data.get("source_type"))
    if source_type not in ("github_issue", "github_pr"):
        return
    data["github_type"] = [source_type]
    data["github_id"] = data.get("source_id") or ""
    data["github_url"] = data.get("source_url") or ""
    data["github_updated_at"] = data.get("source_updated_at") or ""
    for key in ("source_type", "source_id", "source_url", "source_updated_at", "source_repo", "source_number"):
        data.pop(key, None)


def apply_legacy_backlog(data: dict) -> None:
    source_type = single_choice(data.get("source_type"))
    if source_type != "backlog_issue":
        return
    data["backlog_id"] = data.get("source_id") or ""
    data["backlog_url"] = data.get("source_url") or ""
    data["backlog_updated_at"] = data.get("source_updated_at") or ""
    for key in ("source_type", "source_id", "source_url", "source_updated_at"):
        data.pop(key, None)


def ensure_pointer_fields(data: dict) -> None:
    if "github_type" not in data:
        empty_github(data)
    if "backlog_id" not in data:
        empty_backlog(data)


def migrate_file(path: Path) -> None:
    data, body = read_doc(path)
    ensure_pointer_fields(data)

    if single_choice(data.get("source_type")) == "routine":
        empty_github(data)
        empty_backlog(data)
        write_doc(path, data, body)
        return

    st = single_choice(data.get("source_type"))
    if st in ("github_issue", "github_pr"):
        apply_legacy_github(data)
    elif st == "backlog_issue":
        apply_legacy_backlog(data)
    elif not st:
        if not data.get("github_id"):
            empty_github(data)
        if not data.get("backlog_id"):
            empty_backlog(data)
        data.pop("source_type", None)
        data.pop("source_id", None)
        data.pop("source_url", None)
        data.pop("source_updated_at", None)

    data.pop("source_repo", None)
    data.pop("source_number", None)
    data.pop("source_type", None)
    data.pop("source_id", None)
    data.pop("source_url", None)
    data.pop("source_updated_at", None)

    write_doc(path, data, body)


def merge_pair(keeper: Path, loser: Path) -> None:
    kdata, kbody = read_doc(keeper)
    ldata, _ = read_doc(loser)
    ensure_pointer_fields(kdata)

    lst = single_choice(ldata.get("source_type"))
    if lst == "backlog_issue" or ldata.get("backlog_id"):
        kdata["backlog_id"] = ldata.get("backlog_id") or ldata.get("source_id") or ""
        kdata["backlog_url"] = ldata.get("backlog_url") or ldata.get("source_url") or ""
        kdata["backlog_updated_at"] = (
            ldata.get("backlog_updated_at") or ldata.get("source_updated_at") or ""
        )

    related = kdata.get("related") or []
    if isinstance(related, list):
        loser_name = loser.stem
        kdata["related"] = [
            link
            for link in related
            if isinstance(link, str) and loser_name not in link
        ]
        if not kdata["related"]:
            kdata["related"] = []

    migrate_file(keeper)
    kdata2, kbody2 = read_doc(keeper)
    kdata2["backlog_id"] = kdata["backlog_id"]
    kdata2["backlog_url"] = kdata["backlog_url"]
    kdata2["backlog_updated_at"] = kdata["backlog_updated_at"]
    kdata2["related"] = kdata.get("related", [])
    write_doc(keeper, kdata2, kbody2)


def scrub_related_to_deleted(deleted_stems: set[str]) -> None:
    for path in ITEMS.rglob("*.md"):
        data, body = read_doc(path)
        related = data.get("related")
        if not isinstance(related, list):
            continue
        new_related = [
            link
            for link in related
            if isinstance(link, str)
            and not any(stem in link for stem in deleted_stems)
        ]
        if new_related != related:
            data["related"] = new_related if new_related else []
            write_doc(path, data, body)


def update_task_tree() -> None:
    tree_path = VAULT / "tasks" / "_タスク.md"
    text = tree_path.read_text(encoding="utf-8")
    for loser in LOSER_PATHS:
        stem = loser.stem
        pattern = re.compile(r"^- \[\[tasks/items/[^\]]*" + re.escape(stem) + r"[^\]]*\]\].*\n", re.MULTILINE)
        text = pattern.sub("", text)
    tree_path.write_text(text, encoding="utf-8")


def main() -> int:
    pairs = [
        (
            ITEMS
            / "改善要望"
            / "ニュース投稿画面の「この画像をGoogleマップの投稿に使用する」という文言を修正（GitHub Issue1365）.md",
            LOSER_PATHS[0],
        ),
        (
            ITEMS
            / "agent-poc"
            / "Gemini が遅いと約120秒待って「Request timed out.」で失敗する（本番で OpenRouter への退避が一度も動いていない）.md",
            LOSER_PATHS[1],
        ),
        (
            ITEMS
            / "業務タスク"
            / "dev の Rundeck・cron に手動登録されたジョブを棚卸しし、yaml 管理に一本化する.md",
            LOSER_PATHS[2],
        ),
        (
            ITEMS / "業務タスク" / "dev への DB コピー時に GBP の連携情報も消す.md",
            LOSER_PATHS[3],
        ),
    ]

    for keeper, loser in pairs:
        if loser.exists():
            merge_pair(keeper, loser)
            loser.unlink()

    deleted_stems = {p.stem for p in LOSER_PATHS}
    scrub_related_to_deleted(deleted_stems)

    for path in sorted(ITEMS.rglob("*.md")):
        if path in LOSER_PATHS:
            continue
        migrate_file(path)

    update_task_tree()
    return 0


if __name__ == "__main__":
    sys.exit(main())
