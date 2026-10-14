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
        self.saved = os.environ.get("GH_TOKEN")
        os.environ.pop("GH_TOKEN", None)

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("GH_TOKEN", None)
        else:
            os.environ["GH_TOKEN"] = self.saved
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
            return completed("[]")

        fetch_github.fetch(self.vault, runner)

        self.assertEqual(calls[0][:3], ("api", "user", "--jq"))
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
        self.assertEqual(my_prs, [])
        self.assertEqual(reviews, [])
        self.assertIn("--author=@me", calls[2])
        self.assertIn("--review-requested=@me", calls[3])

    def test_missing_user_does_not_write_cache(self):
        def runner(args):
            return completed("", returncode=1, stderr="HTTP 403")

        with self.assertRaises(RuntimeError) as raised:
            fetch_github.fetch(self.vault, runner)

        self.assertIn("GH_TOKEN", str(raised.exception))
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
            return completed("", returncode=1, stderr="rate limit")

        with self.assertRaises(RuntimeError):
            fetch_github.fetch(self.vault, runner)

        self.assertTrue((self.vault / "sources/github/assigned-issues.json").exists())
        self.assertFalse((self.vault / "sources/github/my-prs.json").exists())

    def test_fetch_loads_dotenv_token_before_gh(self):
        (self.vault / ".env").write_text("GH_TOKEN=from-file\n", encoding="utf-8")
        seen: list[str] = []

        def runner(args):
            seen.append(os.environ.get("GH_TOKEN", ""))
            if args[:2] == ("api", "user"):
                return completed("octocat\n")
            return completed("[]")

        fetch_github.fetch(self.vault, runner)

        self.assertEqual(seen[0], "from-file")

    def test_runtime_token_wins_over_dotenv(self):
        os.environ["GH_TOKEN"] = "runtime-secret"
        (self.vault / ".env").write_text("GH_TOKEN=from-file\n", encoding="utf-8")

        def runner(args):
            if args[:2] == ("api", "user"):
                self.assertEqual(os.environ["GH_TOKEN"], "runtime-secret")
                return completed("octocat\n")
            return completed("[]")

        fetch_github.fetch(self.vault, runner)


if __name__ == "__main__":
    unittest.main()
