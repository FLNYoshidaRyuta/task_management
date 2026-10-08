import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inbox_hints


def write_json(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def write_task(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n本文\n", encoding="utf-8")


class InboxHintsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        write_json(self.vault / "sources/github/assigned-issues.json", [])
        write_json(self.vault / "sources/github/my-prs.json", [])
        write_json(self.vault / "sources/github/review-requests.json", [])

    def tearDown(self):
        self.temp.cleanup()

    def test_same_title_colon_normalization(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-A",
                    "sourceUrl": "https://example.test/view/MYPL-A",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "まいぷれくん：タイムアウト",
                    "status": {"name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-B",
                    "sourceUrl": "https://example.test/view/MYPL-B",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "まいぷれくん:タイムアウト",
                    "status": {"name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-OTHER",
                    "sourceUrl": "https://example.test/view/MYPL-OTHER",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "別件",
                    "status": {"name": "未対応"},
                },
            ],
        )

        md = inbox_hints.build_hints(
            self.vault,
            ["backlog"],
            [("backlog_issue", "MYPL-A"), ("backlog_issue", "MYPL-B")],
            [],
        )

        self.assertIn("`same_title`", md)
        self.assertEqual(md.count("`same_title`"), 1)
        self.assertNotIn("MYPL-OTHER", md)

    def test_github_ref_from_backlog_description(self):
        write_json(
            self.vault / "sources/github/assigned-issues.json",
            [
                {
                    "sourceType": "github_issue",
                    "sourceId": "FutureLinkNetwork/agent-dev#467",
                    "sourceUrl": "https://github.com/FutureLinkNetwork/agent-dev/issues/467",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "title": "Gemini timeout",
                    "state": "open",
                }
            ],
        )
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-4238",
                    "sourceUrl": "https://example.test/view/MYPL-4238",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "Backlog側",
                    "description": "詳細\nhttps://github.com/FutureLinkNetwork/agent-dev/issues/467\n",
                    "status": {"name": "未対応"},
                }
            ],
        )

        md = inbox_hints.build_hints(
            self.vault,
            ["github", "backlog"],
            [
                ("github_issue", "FutureLinkNetwork/agent-dev#467"),
                ("backlog_issue", "MYPL-4238"),
            ],
            [],
        )

        self.assertIn("`github_ref`", md)
        self.assertIn("FutureLinkNetwork/agent-dev#467", md)

    def test_no_match_for_unrelated_new(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-1",
                    "sourceUrl": "https://example.test/view/MYPL-1",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "A",
                    "status": {"name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-2",
                    "sourceUrl": "https://example.test/view/MYPL-2",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "B",
                    "status": {"name": "未対応"},
                },
            ],
        )

        md = inbox_hints.build_hints(
            self.vault,
            ["backlog"],
            [("backlog_issue", "MYPL-1"), ("backlog_issue", "MYPL-2")],
            [],
        )

        self.assertIn("（一致なし）", md)
        self.assertNotIn("`same_title`", md)
        self.assertNotIn("`github_ref`", md)

    def test_existing_tasks_not_compared_to_each_other(self):
        write_json(self.vault / "sources/backlog/assigned-issues.json", [])
        write_task(
            self.vault / "tasks/items/改善要望/同じ名前.md",
            "\n".join(
                [
                    "title: 共通タイトル",
                    "status:",
                    "  - todo",
                    "source_type:",
                    "  - backlog_issue",
                    "source_id: MYPL-X",
                ]
            ),
        )
        write_task(
            self.vault / "tasks/items/改善要望/同じ名前2.md",
            "\n".join(
                [
                    "title: 共通タイトル",
                    "status:",
                    "  - todo",
                    "source_type:",
                    "  - backlog_issue",
                    "source_id: MYPL-Y",
                ]
            ),
        )

        md = inbox_hints.build_hints(self.vault, ["backlog"], [], [])

        self.assertNotIn("`same_title`", md)

    def test_update_section_fields(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-UPD",
                    "sourceUrl": "https://example.test/view/MYPL-UPD",
                    "sourceUpdatedAt": "2026-10-08T09:34:44Z",
                    "summary": "キャッシュタイトル",
                    "description": "追記された本文の一部です。",
                    "status": {"name": "調査中"},
                }
            ],
        )
        write_task(
            self.vault / "tasks/items/改善要望/更新対象.md",
            "\n".join(
                [
                    "title: タスクタイトル",
                    "status:",
                    "  - todo",
                    "source_type:",
                    "  - backlog_issue",
                    "source_id: MYPL-UPD",
                    "source_updated_at: 2026-10-06T02:21:01Z",
                ]
            ),
        )

        md = inbox_hints.build_hints(
            self.vault,
            ["backlog"],
            [],
            [("backlog_issue", "MYPL-UPD")],
        )

        self.assertIn("## 更新差分", md)
        self.assertIn("cache source_updated_at: 2026-10-08T09:34:44Z", md)
        self.assertIn("task source_updated_at: 2026-10-06T02:21:01Z", md)
        self.assertIn("external state: 調査中", md)
        self.assertIn("cache body excerpt:", md)
        self.assertIn("追記された本文", md)

    def test_output_has_no_relation_keywords(self):
        write_json(
            self.vault / "sources/backlog/assigned-issues.json",
            [
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-A",
                    "sourceUrl": "https://example.test/view/MYPL-A",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "同じ",
                    "status": {"name": "未対応"},
                },
                {
                    "sourceType": "backlog_issue",
                    "sourceId": "MYPL-B",
                    "sourceUrl": "https://example.test/view/MYPL-B",
                    "sourceUpdatedAt": "2026-10-08T00:00:00Z",
                    "summary": "同じ",
                    "status": {"name": "未対応"},
                },
            ],
        )

        md = inbox_hints.build_hints(
            self.vault,
            ["backlog"],
            [("backlog_issue", "MYPL-A"), ("backlog_issue", "MYPL-B")],
            [],
        )

        lowered = md.lower()
        self.assertNotIn("related", lowered)
        self.assertNotIn("depends_on", lowered)
        self.assertNotIn("親子", md)
        self.assertNotIn("個人タスクの status", md)

    def test_unknown_new_exits_with_error(self):
        write_json(self.vault / "sources/backlog/assigned-issues.json", [])
        script = Path(__file__).resolve().parent / "inbox_hints.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--vault",
                str(self.vault),
                "--sources",
                "backlog",
                "--new",
                "backlog_issue:MYPL-MISSING",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown new candidate", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
