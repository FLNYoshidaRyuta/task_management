import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_comments


class FetchCommentsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_parse_github_source_id(self):
        owner_repo, number = fetch_comments.parse_github_source_id(
            "FutureLinkNetwork/agent-dev#467"
        )
        self.assertEqual(owner_repo, "FutureLinkNetwork/agent-dev")
        self.assertEqual(number, "467")

    def test_normalize_and_sort_github_comments(self):
        raw = [
            {
                "id": 2,
                "user": {"login": "b"},
                "created_at": "2026-10-09T02:00:00Z",
                "updated_at": "2026-10-09T02:00:00Z",
                "html_url": "https://github.com/o/r/issues/1#issuecomment-2",
                "body": "second",
            },
            {
                "id": 1,
                "user": {"login": "a"},
                "created_at": "2026-10-09T01:00:00Z",
                "updated_at": "2026-10-09T01:00:00Z",
                "html_url": "https://github.com/o/r/issues/1#issuecomment-1",
                "body": "first",
            },
        ]
        normalized = fetch_comments.sort_comments(
            [fetch_comments.normalize_github_comment(item) for item in raw]
        )
        self.assertEqual([item["id"] for item in normalized], ["1", "2"])
        self.assertEqual(normalized[0]["author"], "a")

    def test_normalize_backlog_comment(self):
        item = fetch_comments.normalize_backlog_comment(
            {
                "id": 99,
                "content": "調査中です",
                "created": "2026-10-09T04:15:43Z",
                "updated": "2026-10-09T04:15:43Z",
                "createdUser": {"name": "吉田"},
            },
            "https://example.backlog.com",
            "MYPL-4221",
        )
        self.assertEqual(item["author"], "吉田")
        self.assertEqual(item["body"], "調査中です")
        self.assertIn("MYPL-4221#comment-99", item["url"])

    def test_merge_replaces_only_requested_ids(self):
        existing = [
            {
                "sourceType": "github_issue",
                "sourceId": "org/repo#1",
                "comments": [{"id": "old", "author": "", "createdAt": "", "updatedAt": "", "url": "", "body": ""}],
            }
        ]
        updates = [
            (
                "github_issue",
                "org/repo#2",
                [
                    {
                        "id": "2",
                        "author": "u",
                        "createdAt": "2026-10-09T01:00:00Z",
                        "updatedAt": "2026-10-09T01:00:00Z",
                        "url": "",
                        "body": "new",
                    }
                ],
            )
        ]
        merged = fetch_comments.merge_comment_entries(existing, updates)
        self.assertEqual(len(merged), 2)
        by_id = {entry["sourceId"]: entry for entry in merged}
        self.assertEqual(by_id["org/repo#1"]["comments"][0]["id"], "old")
        self.assertEqual(by_id["org/repo#2"]["comments"][0]["body"], "new")

    def test_fetch_updates_writes_github_cache(self):
        def fake_github_fetch(source_type: str, source_id: str) -> list[dict]:
            self.assertEqual(source_type, "github_issue")
            self.assertEqual(source_id, "FutureLinkNetwork/agent-dev#467")
            return [
                {
                    "id": "1",
                    "author": "bot",
                    "createdAt": "2026-10-09T01:00:00Z",
                    "updatedAt": "2026-10-09T01:00:00Z",
                    "url": "https://github.com/x/y/issues/467#issuecomment-1",
                    "body": "進捗あり",
                }
            ]

        fetch_comments.fetch_updates(
            self.vault,
            ["github"],
            [("github_issue", "FutureLinkNetwork/agent-dev#467")],
            github_fetcher=fake_github_fetch,
        )

        path = self.vault / fetch_comments.COMMENT_CACHE_FILES["github"]
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["sourceId"], "FutureLinkNetwork/agent-dev#467")
        self.assertEqual(data[0]["comments"][0]["body"], "進捗あり")

    def test_fetch_updates_merges_backlog_without_touching_github(self):
        github_path = self.vault / fetch_comments.COMMENT_CACHE_FILES["github"]
        github_path.parent.mkdir(parents=True, exist_ok=True)
        github_path.write_text(
            json.dumps(
                [
                    {
                        "sourceType": "github_issue",
                        "sourceId": "org/repo#1",
                        "comments": [],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        def fake_backlog_fetch(issue_key: str) -> list[dict]:
            self.assertEqual(issue_key, "MYPL-4221")
            return [
                {
                    "id": "10",
                    "author": "吉田",
                    "createdAt": "2026-10-09T04:15:43Z",
                    "updatedAt": "2026-10-09T04:15:43Z",
                    "url": "",
                    "body": "コメント",
                }
            ]

        fetch_comments.fetch_updates(
            self.vault,
            ["backlog"],
            [("backlog_issue", "MYPL-4221")],
            backlog_fetcher=fake_backlog_fetch,
        )

        backlog_data = json.loads(
            (self.vault / fetch_comments.COMMENT_CACHE_FILES["backlog"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(backlog_data[0]["sourceId"], "MYPL-4221")
        github_data = json.loads(github_path.read_text(encoding="utf-8"))
        self.assertEqual(github_data[0]["sourceId"], "org/repo#1")


if __name__ == "__main__":
    unittest.main()
