import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inbox_progress


def write_task(vault: Path, rel: str, frontmatter: str) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n## 概要\n\n", encoding="utf-8")


class InboxProgressTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        github = self.vault / "sources/github"
        github.mkdir(parents=True)
        (github / "viewer.json").write_text('{"login":"me"}\n', encoding="utf-8")
        (github / "assigned-issues.json").write_text("[]", encoding="utf-8")
        (github / "review-requests.json").write_text("[]", encoding="utf-8")
        (github / "my-prs.json").write_text(
            json.dumps(
                [
                    {
                        "sourceType": "github_pr",
                        "sourceId": "o/r#5",
                        "closingIssues": ["o/r#12"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        backlog = self.vault / "sources/backlog"
        backlog.mkdir()
        (backlog / "viewer.json").write_text('{"id": 99}\n', encoding="utf-8")
        (backlog / "assigned-issues.json").write_text("[]", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_new_github_issue_with_own_pr_is_in_progress(self):
        compare = {
            "candidates": [
                {
                    "source_type": "github_issue",
                    "source_id": "o/r#12",
                    "title": "Issue",
                    "source_updated_at": "2026-10-01T00:00:00Z",
                    "linked_tasks": [],
                }
            ],
            "missing_from_cache": [],
        }
        analysis = inbox_progress.analyze(self.vault, ["github"], compare)
        self.assertEqual(analysis["new_status"][("github_issue", "o/r#12")], "in_progress")

    def test_own_comment_after_task_timestamp(self):
        write_task(
            self.vault,
            "tasks/items/p/t.md",
            "\n".join(
                [
                    "title: t",
                    "status:",
                    "  - todo",
                    "backlog_id: MYPL-1",
                    "backlog_url: https://example.backlog.com/view/MYPL-1",
                    "backlog_updated_at: 2026-10-01T00:00:00Z",
                ]
            ),
        )
        comments_path = self.vault / "sources/backlog/comments.json"
        comments_path.write_text(
            json.dumps(
                [
                    {
                        "sourceType": "backlog_issue",
                        "sourceId": "MYPL-1",
                        "comments": [
                            {
                                "id": "1",
                                "author": "me",
                                "authorId": "99",
                                "createdAt": "2026-10-02T00:00:00Z",
                                "updatedAt": "2026-10-02T00:00:00Z",
                                "url": "",
                                "body": "進捗",
                            }
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        compare = {
            "candidates": [
                {
                    "source_type": "backlog_issue",
                    "source_id": "MYPL-1",
                    "title": "課題",
                    "source_updated_at": "2026-10-03T00:00:00Z",
                    "linked_tasks": [
                        {
                            "path": "tasks/items/p/t.md",
                            "title": "t",
                            "status": "todo",
                            "source_updated_at": "2026-10-01T00:00:00Z",
                        }
                    ],
                    "cache_newer": True,
                }
            ],
            "missing_from_cache": [],
        }
        analysis = inbox_progress.analyze(self.vault, ["backlog"], compare)
        self.assertEqual(len(analysis["status_changes"]), 1)
        self.assertIn("own_comment", analysis["status_changes"][0]["reasons"])

    def test_pr_only_github_update_candidate(self):
        write_task(
            self.vault,
            "tasks/items/p/gh.md",
            "\n".join(
                [
                    "title: gh",
                    "status:",
                    "  - todo",
                    "github_type:",
                    "  - github_issue",
                    "github_repo: r",
                    "github_id: Issue#12",
                    "github_url: https://github.com/o/r/issues/12",
                    "github_updated_at: 2026-10-01T00:00:00Z",
                ]
            ),
        )
        compare = {
            "candidates": [
                {
                    "source_type": "github_issue",
                    "source_id": "o/r#12",
                    "title": "Issue",
                    "source_updated_at": "2026-10-01T00:00:00Z",
                    "linked_tasks": [
                        {
                            "path": "tasks/items/p/gh.md",
                            "title": "gh",
                            "status": "todo",
                            "source_updated_at": "2026-10-01T00:00:00Z",
                        }
                    ],
                    "cache_newer": False,
                }
            ],
            "missing_from_cache": [],
        }
        analysis = inbox_progress.analyze(self.vault, ["github"], compare)
        self.assertEqual(len(analysis["updated_candidates"]), 1)
        self.assertTrue(analysis["updated_candidates"][0].get("progress_only"))
        self.assertEqual(len(analysis["status_changes"]), 1)
        self.assertIn("own_open_pr", analysis["status_changes"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
