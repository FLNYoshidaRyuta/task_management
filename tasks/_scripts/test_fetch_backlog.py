import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_backlog


class FetchBacklogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        self.keys = ("BACKLOG_BASE_URL", "BACKLOG_API_KEY")
        self.saved = {key: os.environ.get(key) for key in self.keys}
        for key in self.keys:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def write_config(self, projects, statuses):
        config = self.vault / "tasks/_config"
        config.mkdir(parents=True)
        (config / "backlog-projects.json").write_text(
            json.dumps({"projects": projects}),
            encoding="utf-8",
        )
        (config / "backlog-statuses.json").write_text(
            json.dumps({"statuses": statuses}),
            encoding="utf-8",
        )

    def test_runtime_secret_wins_over_dotenv(self):
        os.environ["BACKLOG_BASE_URL"] = "https://runtime.backlog.jp"
        os.environ["BACKLOG_API_KEY"] = "runtime-key"
        (self.vault / ".env").write_text(
            "BACKLOG_BASE_URL=https://file.backlog.jp\nBACKLOG_API_KEY=file-key\n",
            encoding="utf-8",
        )

        base_url, api_key = fetch_backlog.require_backlog_credentials(self.vault)

        self.assertEqual(base_url, "https://runtime.backlog.jp")
        self.assertEqual(api_key, "runtime-key")

    def test_dotenv_supplies_missing_credentials(self):
        (self.vault / ".env").write_text(
            "BACKLOG_BASE_URL=https://example.backlog.jp\nBACKLOG_API_KEY=file-key\n",
            encoding="utf-8",
        )

        base_url, api_key = fetch_backlog.require_backlog_credentials(self.vault)

        self.assertEqual(base_url, "https://example.backlog.jp")
        self.assertEqual(api_key, "file-key")

    def test_missing_credentials_raise(self):
        with self.assertRaises(RuntimeError) as raised:
            fetch_backlog.require_backlog_credentials(self.vault)
        self.assertIn("BACKLOG_API_KEY", str(raised.exception))

    def test_build_url_repeats_filters_and_appends_api_key(self):
        url = fetch_backlog.build_url(
            "https://example.backlog.jp/",
            "secret-key",
            "/api/v2/issues",
            {"assigneeId[]": [7], "projectId[]": [1, 2], "count": 100},
        )
        self.assertTrue(url.startswith("https://example.backlog.jp/api/v2/issues?"))
        self.assertIn("assigneeId%5B%5D=7", url)
        self.assertIn("projectId%5B%5D=1", url)
        self.assertIn("projectId%5B%5D=2", url)
        self.assertIn("apiKey=secret-key", url)
        self.assertNotIn("all=true", url)

    def test_fetch_writes_included_issues_only(self):
        self.write_config(
            [
                {"projectId": 1, "projectKey": "MYPL", "include": True},
                {"projectId": 2, "projectKey": "SKIP", "include": False},
            ],
            [
                {"projectId": 1, "statusId": 10, "include": True},
                {"projectId": 1, "statusId": 11, "include": False},
                {"projectId": 2, "statusId": 20, "include": True},
            ],
        )
        calls = []

        def get_json(path, query):
            calls.append((path, query))
            if path == "/api/v2/users/myself":
                return {"id": 7, "name": "吉田"}
            self.assertEqual(query["assigneeId[]"], [7])
            self.assertEqual(query["projectId[]"], [1])
            self.assertEqual(query["statusId[]"], [10])
            return [
                {
                    "id": 100,
                    "issueKey": "MYPL-100",
                    "summary": "調査",
                    "description": "本文",
                    "updated": "2026-10-01T00:00:00Z",
                    "created": "2026-09-01T00:00:00Z",
                    "project": {"id": 1, "projectKey": "MYPL", "name": "マイプラ"},
                    "status": {"id": 10, "name": "処理中"},
                    "priority": {"id": 3, "name": "中"},
                    "assignee": {"id": 7, "name": "吉田"},
                    "startDate": None,
                    "dueDate": "2026-10-20",
                    "estimatedHours": 1.5,
                }
            ]

        fetch_backlog.fetch_assigned(self.vault, get_json, "https://example.backlog.jp")

        payload = json.loads(
            (self.vault / "sources/backlog/assigned-issues.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(payload), 1)
        issue = payload[0]
        self.assertEqual(issue["sourceType"], "backlog_issue")
        self.assertEqual(issue["sourceId"], "MYPL-100")
        self.assertEqual(issue["sourceUrl"], "https://example.backlog.jp/view/MYPL-100")
        self.assertEqual(issue["sourceUpdatedAt"], "2026-10-01T00:00:00Z")
        self.assertEqual(issue["summary"], "調査")
        self.assertEqual(issue["project"]["key"], "MYPL")
        self.assertEqual(issue["status"]["name"], "処理中")
        self.assertEqual(calls[0][0], "/api/v2/users/myself")
        self.assertNotIn("all=true", str(calls))
        viewer = json.loads(
            (self.vault / "sources/backlog/viewer.json").read_text(encoding="utf-8")
        )
        self.assertEqual(viewer["id"], 7)

    def test_empty_include_does_not_modify_cache(self):
        self.write_config(
            [{"projectId": 1, "projectKey": "MYPL", "include": False}],
            [{"projectId": 1, "statusId": 10, "include": True}],
        )
        cache = self.vault / "sources/backlog/assigned-issues.json"
        cache.parent.mkdir(parents=True)
        cache.write_text("[]\n", encoding="utf-8")

        def get_json(path, query):
            self.assertEqual(path, "/api/v2/users/myself")
            return {"id": 7, "name": "吉田"}

        fetch_backlog.fetch_assigned(self.vault, get_json, "https://example.backlog.jp")

        self.assertEqual(cache.read_text(encoding="utf-8"), "[]\n")

    def test_refresh_preserves_include_and_skips_closed_by_default(self):
        self.write_config(
            [{"projectId": 2, "projectKey": "OLD", "include": False}],
            [{"projectId": 1, "statusId": 4, "include": True}],
        )
        calls = []

        def get_json(path, query):
            calls.append(path)
            self.assertIsNone(query)
            if path == "/api/v2/projects":
                return [
                    {"id": 2, "projectKey": "OLD", "name": "旧"},
                    {"id": 1, "projectKey": "NEW", "name": "新"},
                ]
            if path == "/api/v2/projects/1/statuses":
                return [
                    {"id": 3, "name": "未対応"},
                    {"id": 4, "name": "完了"},
                    {"id": 5, "name": "却下"},
                ]
            raise AssertionError(path)

        fetch_backlog.refresh_statuses(self.vault, get_json)

        projects = json.loads(
            (self.vault / "tasks/_config/backlog-projects.json").read_text(encoding="utf-8")
        )["projects"]
        self.assertEqual([row["projectKey"] for row in projects], ["NEW", "OLD"])
        self.assertTrue(projects[0]["include"])
        self.assertFalse(projects[1]["include"])
        statuses = json.loads(
            (self.vault / "tasks/_config/backlog-statuses.json").read_text(encoding="utf-8")
        )["statuses"]
        by_id = {row["statusId"]: row["include"] for row in statuses}
        self.assertEqual(set(by_id), {3, 4, 5})
        self.assertTrue(by_id[3])
        self.assertTrue(by_id[4])
        self.assertFalse(by_id[5])
        self.assertNotIn("/api/v2/projects/2/statuses", calls)
        self.assertNotIn("/api/v2/issues", calls)
        self.assertFalse((self.vault / "sources/backlog/assigned-issues.json").exists())

    def test_pages_until_short_page(self):
        self.write_config(
            [{"projectId": 1, "projectKey": "MYPL", "include": True}],
            [{"projectId": 1, "statusId": 10, "include": True}],
        )
        offsets = []

        def get_json(path, query):
            if path == "/api/v2/users/myself":
                return {"id": 7, "name": "吉田"}
            offsets.append(query["offset"])
            if query["offset"] == 0:
                return [
                    {"id": index, "issueKey": f"MYPL-{index}", "summary": "s", "updated": "2026-10-01T00:00:00Z"}
                    for index in range(fetch_backlog.PAGE_COUNT)
                ]
            return [
                {"id": 1000, "issueKey": "MYPL-1000", "summary": "last", "updated": "2026-10-02T00:00:00Z"}
            ]

        fetch_backlog.fetch_assigned(self.vault, get_json, "https://example.backlog.jp")

        self.assertEqual(offsets, [0, fetch_backlog.PAGE_COUNT])
        payload = json.loads(
            (self.vault / "sources/backlog/assigned-issues.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(payload), fetch_backlog.PAGE_COUNT + 1)
        self.assertEqual(payload[-1]["sourceId"], "MYPL-1000")


if __name__ == "__main__":
    unittest.main()
