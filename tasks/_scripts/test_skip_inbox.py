import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import skip_inbox


def write_json(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


class SkipInboxTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _backlog_cache(self, source_id: str, title: str) -> None:
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": source_id,
                    "sourceUrl": f"https://example.test/view/{source_id}",
                    "sourceUpdatedAt": "2026-10-06T03:00:00Z",
                    "summary": title,
                    "status": {"name": "未対応"},
                }
            ],
        )
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])

    def test_add_records_item(self):
        self._backlog_cache("MYPL-1", "スキップする課題")
        skip_inbox.add_skipped(
            self.vault, [("backlog_issue", "MYPL-1")], ["backlog"]
        )
        data = skip_inbox.load_skipped_file(self.vault)
        self.assertEqual(len(data["items"]), 1)
        item = data["items"][0]
        self.assertEqual(item["source_type"], "backlog_issue")
        self.assertEqual(item["source_id"], "MYPL-1")
        self.assertEqual(item["title"], "スキップする課題")
        self.assertEqual(item["source_url"], "https://example.test/view/MYPL-1")
        self.assertRegex(item["skipped_at"], r"^\d{4}-\d{2}-\d{2}T")

    def test_readd_preserves_skipped_at(self):
        self._backlog_cache("MYPL-1", "古いタイトル")
        skip_inbox.add_skipped(
            self.vault, [("backlog_issue", "MYPL-1")], ["backlog"]
        )
        first_at = skip_inbox.load_skipped_file(self.vault)["items"][0]["skipped_at"]

        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-1",
                    "sourceUrl": "https://example.test/view/MYPL-1",
                    "sourceUpdatedAt": "2026-10-07T00:00:00Z",
                    "summary": "新しいタイトル",
                    "status": {"name": "未対応"},
                }
            ],
        )
        skip_inbox.add_skipped(
            self.vault, [("backlog_issue", "MYPL-1")], ["backlog"]
        )
        item = skip_inbox.load_skipped_file(self.vault)["items"][0]
        self.assertEqual(item["skipped_at"], first_at)
        self.assertEqual(item["title"], "新しいタイトル")

    def test_add_not_in_cache_fails(self):
        self._backlog_cache("MYPL-1", "ある")
        with self.assertRaises(ValueError):
            skip_inbox.add_skipped(
                self.vault, [("backlog_issue", "MYPL-999")], ["backlog"]
            )

    def test_remove_and_missing(self):
        self._backlog_cache("MYPL-1", "ある")
        skip_inbox.add_skipped(
            self.vault, [("backlog_issue", "MYPL-1")], ["backlog"]
        )
        skip_inbox.remove_skipped(self.vault, [("backlog_issue", "MYPL-1")])
        self.assertEqual(skip_inbox.load_skipped_file(self.vault)["items"], [])

        with self.assertRaises(ValueError):
            skip_inbox.remove_skipped(self.vault, [("backlog_issue", "MYPL-1")])

    def test_list_markdown(self):
        self._backlog_cache("MYPL-1", "一覧用")
        skip_inbox.add_skipped(
            self.vault, [("backlog_issue", "MYPL-1")], ["backlog"]
        )
        md = skip_inbox.format_list_markdown(self.vault)
        self.assertIn("## タスク化しないとして保持", md)
        self.assertIn("`MYPL-1`", md)
        self.assertIn("一覧用", md)

    def test_parse_identity(self):
        t, i = skip_inbox.parse_identity("github_issue:owner/repo#12")
        self.assertEqual(t, "github_issue")
        self.assertEqual(i, "owner/repo#12")


if __name__ == "__main__":
    unittest.main()
