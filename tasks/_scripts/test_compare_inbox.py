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
            "\n".join(
                [
                    "title: 更新された課題",
                    "status: todo",
                    "source_type: backlog_issue",
                    "source_id: MYPL-2",
                    "source_updated_at: 2026-10-06T00:00:00Z",
                ]
            ),
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        by_id = {item["source_id"]: item for item in result}

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
            "\n".join(
                [
                    "title: 旧キー",
                    "status: todo",
                    "source_type: github_issue",
                    "source_repo: owner/repo",
                    "source_number: 12",
                ]
            ),
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
        by_id = {(item["source_type"], item["source_id"]): item for item in result}

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
                    "source_type: routine",
                    "source_id: MYPL-9",
                ]
            ),
        )

        result = compare_inbox.compare(self.vault, ["backlog"])
        self.assertEqual(result[0]["linked_tasks"], [])

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
        self.assertEqual(result[0]["source_id"], "MYPL-3")

    def test_missing_cache_raises(self):
        with self.assertRaises(FileNotFoundError):
            compare_inbox.compare(self.vault, ["github"])


if __name__ == "__main__":
    unittest.main()
