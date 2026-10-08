import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare_inbox


def write_json(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def write_task(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n本文\n", encoding="utf-8")


def backlog_fm(title: str, backlog_id: str, updated: str = "", url: str = "") -> str:
    backlog_url = url or f"https://example.test/view/{backlog_id}"
    lines = [
        f"title: {title}",
        "status:",
        "  - todo",
        f"backlog_id: {backlog_id}",
        f"backlog_url: {backlog_url}",
    ]
    if updated:
        lines.append(f"backlog_updated_at: {updated}")
    return "\n".join(lines)


def github_fm(
    title: str,
    github_id: str,
    github_type: str = "github_issue",
    updated: str = "",
    url: str = "",
) -> str:
    repo, number = github_id.split("#", 1)
    github_url = url or f"https://github.com/{repo}/issues/{number}"
    lines = [
        f"title: {title}",
        "status:",
        "  - todo",
        "github_type:",
        f"  - {github_type}",
        f"github_id: {github_id}",
        f"github_url: {github_url}",
    ]
    if updated:
        lines.append(f"github_updated_at: {updated}")
    return "\n".join(lines)


class CompareInboxTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_new_candidate_and_newer_cache(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-1",
                    "sourceUrl": "https://example.test/view/MYPL-1",
                    "sourceUpdatedAt": "2026-10-06T03:00:00Z",
                    "summary": "新しい課題",
                    "status": {"id": 1, "name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-2",
                    "sourceUrl": "https://example.test/view/MYPL-2",
                    "sourceUpdatedAt": "2026-10-07T00:00:00Z",
                    "summary": "更新された課題",
                    "status": {"id": 2, "name": "処理中"},
                },
            ],
        )
        write_task(
            self.vault / "tasks/items/改善要望/更新された課題.md",
            backlog_fm("更新された課題", "MYPL-2", updated="2026-10-06T00:00:00Z"),
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        by_id = {item["source_id"]: item for item in result["candidates"]}

        self.assertEqual(by_id["MYPL-1"]["linked_tasks"], [])
        self.assertIsNone(by_id["MYPL-1"]["cache_newer"])
        self.assertEqual(by_id["MYPL-1"]["external_state"], "未対応")
        self.assertEqual(by_id["MYPL-1"]["title"], "新しい課題")

        linked = by_id["MYPL-2"]["linked_tasks"]
        self.assertEqual(linked[0]["path"], "tasks/items/改善要望/更新された課題.md")
        self.assertTrue(by_id["MYPL-2"]["cache_newer"])

    def test_merge_same_github_pr_and_link_legacy_task(self):
        pull = {
            "sourceType": "github_pr",
            "sourceId": "owner/repo#4",
            "sourceUrl": "https://github.com/owner/repo/pull/4",
            "sourceUpdatedAt": "2026-10-01T00:00:00Z",
            "title": "古いタイトル",
            "state": "open",
        }
        review = {
            **pull,
            "sourceUpdatedAt": "2026-10-02T00:00:00Z",
            "title": "新しいタイトル",
        }
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [pull])
        write_json(self.vault / "sources/github/review-requests.json", [review])
        write_task(
            self.vault / "tasks/items/画質向上/旧キー.md",
            github_fm("旧キー", "owner/repo#12"),
        )
        write_json(
            self.vault / "sources/github/assigned-issues.json",
            [
                {
                    "sourceType": "github_issue",
                    "sourceId": "owner/repo#12",
                    "sourceUrl": "https://github.com/owner/repo/issues/12",
                    "sourceUpdatedAt": "2026-10-03T00:00:00Z",
                    "title": "Issue",
                    "state": "open",
                }
            ],
        )

        result = compare_inbox.compare(self.vault, ["github"])
        by_id = {
            (item["source_type"], item["source_id"]): item
            for item in result["candidates"]
        }

        pull_item = by_id[("github_pr", "owner/repo#4")]
        self.assertEqual(pull_item["title"], "新しいタイトル")
        self.assertEqual(pull_item["source_updated_at"], "2026-10-02T00:00:00Z")
        self.assertEqual(pull_item["linked_tasks"], [])

        issue = by_id[("github_issue", "owner/repo#12")]
        self.assertEqual(issue["linked_tasks"][0]["path"], "tasks/items/画質向上/旧キー.md")
        self.assertIsNone(issue["cache_newer"])

    def test_routine_task_is_ignored(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-9",
                    "sourceUrl": "https://example.test/view/MYPL-9",
                    "sourceUpdatedAt": "2026-10-06T00:00:00Z",
                    "summary": "日次",
                    "status": {"name": "未対応"},
                }
            ],
        )
        write_task(
            self.vault / "tasks/items/routine/2026-10-06_日次.md",
            "\n".join(
                [
                    "title: 日次",
                    "source_type:",
                    "  - routine",
                    "source_id: MYPL-9",
                ]
            ),
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        self.assertEqual(result["candidates"][0]["linked_tasks"], [])
        self.assertEqual(result["missing_from_cache"], [])

    def test_utf8_bom_cache_is_readable(self):
        path = self.vault / "sources/backlog/assigned-issues.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            "\ufeff".encode("utf-8")
            + json.dumps(
                [
                    {
                        "sourceType": "backlog_issue",
                        "sourceId": "MYPL-3",
                        "sourceUrl": "https://example.test/view/MYPL-3",
                        "sourceUpdatedAt": "2026-10-06T00:00:00Z",
                        "summary": "BOM",
                        "status": {"name": "未対応"},
                    }
                ],
                ensure_ascii=False,
            ).encode("utf-8")
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        self.assertEqual(result["candidates"][0]["source_id"], "MYPL-3")

    def test_missing_from_cache_when_task_not_in_cache(self):
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_task(
            self.vault / "tasks/items/画質向上/欠落.md",
            github_fm(
                "欠落",
                "owner/repo#99",
                url="https://github.com/owner/repo/issues/99",
            ),
        )

        result = compare_inbox.compare(self.vault, ["github"])
        missing = result["missing_from_cache"]

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["source_id"], "owner/repo#99")
        self.assertEqual(missing[0]["tasks"][0]["path"], "tasks/items/画質向上/欠落.md")

    def test_missing_from_cache_excludes_done_and_canceled(self):
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_task(
            self.vault / "tasks/items/画質向上/完了.md",
            github_fm("完了", "owner/repo#1").replace("  - todo", "  - done"),
        )
        write_task(
            self.vault / "tasks/items/画質向上/却下.md",
            github_fm("却下", "owner/repo#2").replace("  - todo", "  - canceled"),
        )

        result = compare_inbox.compare(self.vault, ["github"])
        self.assertEqual(result["missing_from_cache"], [])

    def test_missing_from_cache_skips_other_source_when_github_only(self):
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_task(
            self.vault / "tasks/items/改善要望/Backlogだけ.md",
            backlog_fm("Backlogだけ", "MYPL-404"),
        )

        result = compare_inbox.compare(self.vault, ["github"])
        self.assertEqual(result["missing_from_cache"], [])

    def test_missing_cache_raises(self):
        with self.assertRaises(FileNotFoundError):
            compare_inbox.compare(self.vault, ["github"])

    def test_format_markdown_sections_and_numbering(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-NEW",
                    "sourceUrl": "https://example.test/view/MYPL-NEW",
                    "sourceUpdatedAt": "2026-10-06T03:00:00Z",
                    "summary": "新規だけ",
                    "status": {"name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-UPD",
                    "sourceUrl": "https://example.test/view/MYPL-UPD",
                    "sourceUpdatedAt": "2026-10-07T00:00:00Z",
                    "summary": "更新あり",
                    "status": {"name": "処理中"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-LINKED",
                    "sourceUrl": "https://example.test/view/MYPL-LINKED",
                    "sourceUpdatedAt": "2026-10-05T00:00:00Z",
                    "summary": "紐づき同期済み",
                    "status": {"name": "未対応"},
                },
            ],
        )
        write_task(
            self.vault / "tasks/items/改善要望/更新あり.md",
            backlog_fm("更新あり", "MYPL-UPD", updated="2026-10-06T00:00:00Z"),
        )
        write_task(
            self.vault / "tasks/items/改善要望/同期済み.md",
            backlog_fm("同期済み", "MYPL-LINKED", updated="2026-10-05T00:00:00Z"),
        )
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_task(
            self.vault / "tasks/items/画質向上/欠落表示.md",
            github_fm(
                "欠落表示",
                "owner/repo#77",
                url="https://github.com/owner/repo/issues/77",
            ),
        )

        result = compare_inbox.compare(self.vault, ["backlog", "github"])
        md = compare_inbox.format_markdown(result)

        self.assertIn("## 新規候補", md)
        self.assertIn("1. **backlog_issue** | `MYPL-NEW`", md)
        self.assertIn("title: 新規だけ", md)
        self.assertIn("state: 未対応", md)
        self.assertNotIn("MYPL-UPD", md.split("## 更新あり")[0])

        self.assertIn("## 更新あり", md)
        self.assertIn("U1. **backlog_issue** | `MYPL-UPD`", md)
        self.assertIn("cache updated: 2026-10-07T00:00:00Z", md)
        self.assertIn("tasks/items/改善要望/更新あり.md", md)
        self.assertIn("task updated: 2026-10-06T00:00:00Z", md)
        self.assertNotIn("U2.", md)
        self.assertNotIn("MYPL-LINKED", md.split("## キャッシュに無い")[0].split("## 更新あり")[1])

        self.assertIn("## キャッシュに無い未完了タスク", md)
        self.assertIn("M1. **github_issue** | `owner/repo#77`", md)
        self.assertIn("欠落表示", md)

    def test_dual_source_task_links_both_channels(self):
        write_json(
            self.vault / "sources/github/assigned-issues.json",
            [
                {
                    "sourceType": "github_issue",
                    "sourceId": "org/repo#1",
                    "sourceUrl": "https://github.com/org/repo/issues/1",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "title": "GitHub",
                    "state": "open",
                }
            ],
        )
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-9",
                    "sourceUrl": "https://example.test/view/MYPL-9",
                    "sourceUpdatedAt": "2026-10-08T01:00:00Z",
                    "summary": "Backlog",
                    "status": {"name": "未対応"},
                }
            ],
        )
        write_task(
            self.vault / "tasks/items/業務タスク/両方.md",
            "\n".join(
                [
                    "title: 両方",
                    "status:",
                    "  - todo",
                    "github_type:",
                    "  - github_issue",
                    "github_id: org/repo#1",
                    "github_url: https://github.com/org/repo/issues/1",
                    "github_updated_at: 2026-10-07T00:00:00Z",
                    "backlog_id: MYPL-9",
                    "backlog_url: https://example.test/view/MYPL-9",
                    "backlog_updated_at: 2026-10-07T00:00:00Z",
                ]
            ),
        )

        result = compare_inbox.compare(self.vault, ["github", "backlog"])
        by_key = {
            (item["source_type"], item["source_id"]): item for item in result["candidates"]
        }
        self.assertEqual(len(by_key[("github_issue", "org/repo#1")]["linked_tasks"]), 1)
        self.assertEqual(len(by_key[("backlog_issue", "MYPL-9")]["linked_tasks"]), 1)
        self.assertTrue(by_key[("github_issue", "org/repo#1")]["cache_newer"])
        self.assertTrue(by_key[("backlog_issue", "MYPL-9")]["cache_newer"])

    def test_attach_backlog_to_existing_github_task(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-99",
                    "sourceUrl": "https://example.test/view/MYPL-99",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "Backlog only",
                    "description": "https://github.com/org/repo/issues/5",
                    "status": {"name": "未対応"},
                }
            ],
        )
        write_task(
            self.vault / "tasks/items/業務タスク/GitHubだけ.md",
            github_fm("GitHubだけ", "org/repo#5"),
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        item = result["candidates"][0]
        self.assertEqual(item["linked_tasks"], [])
        self.assertEqual(
            item["attach_to"], "tasks/items/業務タスク/GitHubだけ.md"
        )

    def test_missing_only_for_absent_channel(self):
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-1",
                    "sourceUrl": "https://example.test/view/MYPL-1",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "ある",
                    "status": {"name": "未対応"},
                }
            ],
        )
        write_task(
            self.vault / "tasks/items/業務タスク/片方欠落.md",
            "\n".join(
                [
                    "title: 片方欠落",
                    "status:",
                    "  - todo",
                    "github_type:",
                    "  - github_issue",
                    "github_id: org/repo#404",
                    "github_url: https://github.com/org/repo/issues/404",
                    "backlog_id: MYPL-1",
                    "backlog_url: https://example.test/view/MYPL-1",
                ]
            ),
        )

        result = compare_inbox.compare(self.vault, ["github", "backlog"])
        missing = result["missing_from_cache"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["source_id"], "org/repo#404")

    def test_format_markdown_empty_sections(self):
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])
        write_json(self.vault / "sources/backlog/assigned-issues.json", [])

        result = compare_inbox.compare(self.vault, ["github", "backlog"])
        md = compare_inbox.format_markdown(result)

        self.assertIn("## 新規候補", md)
        self.assertIn("（0件）", md)
        self.assertIn("## 追記候補", md)
        self.assertIn("## 更新あり", md)
        self.assertIn("## キャッシュに無い未完了タスク", md)


if __name__ == "__main__":
    unittest.main()
