import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_github


def completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class FetchGithubTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        self.saved = {
            key: os.environ.get(key) for key in ("GH_TOKEN", "GITHUB_FETCH_TOKEN")
        }
        os.environ.pop("GH_TOKEN", None)
        os.environ.pop("GITHUB_FETCH_TOKEN", None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def test_fetch_writes_three_caches_for_the_authenticated_user(self):
        calls: list[tuple[str, ...]] = []

        def runner(args):
            calls.append(tuple(args))
            if args[:2] == ("api", "user"):
                return completed("octocat\n")
            if "--assignee=@me" in args:
                return completed(
                    json.dumps(
                        [
                            {
                                "number": 12,
                                "title": "件名",
                                "body": "本文",
                                "state": "open",
                                "updatedAt": "2026-10-01T00:00:00Z",
                                "url": "https://github.com/o/r/issues/12",
                                "repository": {"nameWithOwner": "o/r"},
                            }
                        ]
                    )
                )
            if args[:2] == ("pr", "view"):
                return completed(
                    json.dumps(
                        {
                            "closingIssuesReferences": [
                                {
                                    "number": 12,
                                    "repository": {
                                        "name": "r",
                                        "owner": {"login": "o"},
                                    },
                                }
                            ],
                            "isDraft": False,
                            "state": "OPEN",
                        }
                    )
                )
            if "--author=@me" in args:
                return completed(
                    json.dumps(
                        [
                            {
                                "number": 5,
                                "title": "PR",
                                "state": "open",
                                "updatedAt": "2026-10-02T00:00:00Z",
                                "url": "https://github.com/o/r/pull/5",
                                "repository": {"nameWithOwner": "o/r"},
                            }
                        ]
                    )
                )
            return completed("[]")

        fetch_github.fetch(self.vault, runner)

        self.assertEqual(calls[0][:3], ("api", "user", "--jq"))
        viewer = json.loads(
            (self.vault / "sources/github/viewer.json").read_text(encoding="utf-8")
        )
        self.assertEqual(viewer["login"], "octocat")
        assigned = json.loads(
            (self.vault / "sources/github/assigned-issues.json").read_text(encoding="utf-8")
        )
        self.assertEqual(assigned[0]["sourceType"], "github_issue")
        self.assertEqual(assigned[0]["sourceId"], "o/r#12")
        self.assertEqual(assigned[0]["title"], "件名")
        my_prs = json.loads(
            (self.vault / "sources/github/my-prs.json").read_text(encoding="utf-8")
        )
        reviews = json.loads(
            (self.vault / "sources/github/review-requests.json").read_text(encoding="utf-8")
        )
        self.assertEqual(my_prs[0]["closingIssues"], ["o/r#12"])
        self.assertEqual(reviews, [])
        self.assertTrue(any("--author=@me" in call for call in calls))
        self.assertTrue(any("--review-requested=@me" in call for call in calls))

    def test_missing_user_does_not_write_cache(self):
        def runner(args):
            return completed("", returncode=1, stderr="HTTP 403")

        with self.assertRaises(RuntimeError) as raised:
            fetch_github.fetch(self.vault, runner)

        self.assertIn("GITHUB_FETCH_TOKEN", str(raised.exception))
        self.assertFalse((self.vault / "sources/github/assigned-issues.json").exists())

    def test_search_failure_keeps_earlier_cache(self):
        def runner(args):
            if args[:2] == ("api", "user"):
                return completed("octocat\n")
            if "--assignee=@me" in args:
                return completed(
                    json.dumps(
                        [
                            {
                                "number": 1,
                                "title": "一件",
                                "updatedAt": "2026-10-01T00:00:00Z",
                                "url": "https://github.com/o/r/issues/1",
                                "repository": {"nameWithOwner": "o/r"},
                            }
                        ]
                    )
                )
            if args[:2] == ("pr", "view"):
                return completed("{}", returncode=1, stderr="rate limit")
            if "--author=@me" in args:
                return completed(
                    json.dumps(
                        [
                            {
                                "number": 2,
                                "title": "pr",
                                "updatedAt": "2026-10-01T00:00:00Z",
                                "url": "https://github.com/o/r/pull/2",
                                "repository": {"nameWithOwner": "o/r"},
                            }
                        ]
                    )
                )
            return completed("", returncode=1, stderr="rate limit")

        with self.assertRaises(RuntimeError):
            fetch_github.fetch(self.vault, runner)

        self.assertTrue((self.vault / "sources/github/assigned-issues.json").exists())
        self.assertFalse((self.vault / "sources/github/my-prs.json").exists())

    def test_fetch_loads_dotenv_token_before_gh(self):
        (self.vault / ".env").write_text(
            "GITHUB_FETCH_TOKEN=from-file\nGH_TOKEN=do-not-load\n",
            encoding="utf-8",
        )
        seen: list[str] = []

        def runner(args):
            seen.append(os.environ.get("GITHUB_FETCH_TOKEN", ""))
            if args[:2] == ("api", "user"):
                return completed("octocat\n")
            return completed("[]")

        fetch_github.fetch(self.vault, runner)

        self.assertEqual(seen[0], "from-file")
        self.assertNotIn("GH_TOKEN", os.environ)

    def test_runtime_token_wins_over_dotenv(self):
        os.environ["GITHUB_FETCH_TOKEN"] = "runtime-secret"
        (self.vault / ".env").write_text(
            "GITHUB_FETCH_TOKEN=from-file\n",
            encoding="utf-8",
        )

        def runner(args):
            if args[:2] == ("api", "user"):
                self.assertEqual(os.environ["GITHUB_FETCH_TOKEN"], "runtime-secret")
                self.assertNotIn("GH_TOKEN", os.environ)
                return completed("octocat\n")
            return completed("[]")

        fetch_github.fetch(self.vault, runner)


if __name__ == "__main__":
    unittest.main()
