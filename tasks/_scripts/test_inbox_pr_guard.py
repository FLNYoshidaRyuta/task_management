import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare_inbox
import inbox_pr_guard


def completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def candidate(
    source_type: str,
    source_id: str,
    updated: str,
    **extra,
) -> dict:
    item = {
        "source_type": source_type,
        "source_id": source_id,
        "title": extra.pop("title", source_id),
        "source_url": extra.pop("source_url", "https://example.test/item"),
        "source_updated_at": updated,
        "external_state": extra.pop("external_state", "open"),
        "linked_tasks": extra.pop("linked_tasks", []),
        "cache_newer": extra.pop("cache_newer", None),
    }
    item.update(extra)
    return item


def compare_result() -> dict:
    return {
        "candidates": [
            candidate("github_issue", "owner/repo#1", "2026-10-01T00:00:00Z", title="新規"),
            candidate(
                "backlog_issue",
                "MYPL-2",
                "2026-10-02T00:00:00Z",
                title="追記",
                attach_to="tasks/items/業務タスク/既存.md",
            ),
            candidate(
                "backlog_issue",
                "MYPL-3",
                "2026-10-03T00:00:00Z",
                title="更新",
                linked_tasks=[
                    {
                        "path": "tasks/items/業務タスク/更新.md",
                        "title": "更新",
                        "status": "todo",
                        "source_url": "https://example.test/view/MYPL-3",
                        "source_updated_at": "2026-10-01T00:00:00Z",
                    }
                ],
                cache_newer=True,
            ),
            candidate(
                "github_issue",
                "owner/repo#9",
                "2026-10-04T00:00:00Z",
                title="スキップ",
                skipped=True,
            ),
        ],
        "missing_from_cache": [
            {
                "source_type": "github_issue",
                "source_id": "owner/repo#8",
                "tasks": [],
            }
        ],
    }


def open_pr(number: int, body: str, branch: str | None = None) -> dict:
    return {
        "number": number,
        "url": f"https://example.test/pull/{number}",
        "title": f"inbox {number}",
        "body": body,
        "headRefName": branch or f"inbox-branch-{number}",
    }


class InboxPrGuardTest(unittest.TestCase):
    def test_marker_roundtrip_ignores_order(self):
        identities = [
            "github_issue:owner/repo#1@2026-10-01T00:00:00Z",
            "backlog_issue:MYPL-3@2026-10-03T00:00:00Z",
        ]
        rendered = inbox_pr_guard.render_marker("new", identities)
        parsed = inbox_pr_guard.marker_identities(rendered, "new")
        self.assertEqual(parsed, sorted(identities))
        reversed_body = inbox_pr_guard.render_marker("new", list(reversed(identities)))
        self.assertEqual(
            inbox_pr_guard.marker_identities(reversed_body, "new"),
            sorted(identities),
        )

    def test_plan_classifies_and_creates_when_no_pr(self):
        plan = inbox_pr_guard.build_plan(compare_result(), {"new": [], "update": []})

        self.assertEqual(plan["new"]["action"], "create")
        self.assertEqual(plan["new"]["reason"], "no_open_pr")
        self.assertEqual(plan["new"]["label"], "inbox-new")
        self.assertIsNone(plan["new"]["pr"])
        self.assertEqual(
            plan["new"]["identities"],
            ["github_issue:owner/repo#1@2026-10-01T00:00:00Z"],
        )
        self.assertEqual(plan["new"]["candidates"][0]["title"], "新規")
        self.assertNotIn("_link_text", plan["new"]["candidates"][0])

        self.assertEqual(plan["update"]["action"], "create")
        self.assertEqual(
            plan["update"]["identities"],
            ["backlog_issue:MYPL-3@2026-10-03T00:00:00Z"],
        )
        self.assertEqual(
            plan["update"]["candidates"][0]["linked_tasks"][0]["path"],
            "tasks/items/業務タスク/更新.md",
        )
        self.assertEqual(plan["attach"][0]["source_id"], "MYPL-2")
        self.assertEqual(plan["missing_from_cache"][0]["source_id"], "owner/repo#8")
        self.assertIn("inbox-pr-guard:new", plan["new"]["body_marker"])

    def test_same_fingerprint_skips(self):
        created = inbox_pr_guard.build_plan(compare_result(), {"new": [], "update": []})
        plan = inbox_pr_guard.build_plan(
            compare_result(),
            {
                "new": [open_pr(4, created["new"]["body_marker"], "inbox-new-existing")],
                "update": [],
            },
        )
        self.assertEqual(plan["new"]["action"], "skip")
        self.assertEqual(plan["new"]["reason"], "unchanged")
        self.assertEqual(plan["new"]["pr"]["number"], 4)
        self.assertEqual(plan["new"]["pr"]["headRefName"], "inbox-new-existing")

    def test_changed_fingerprint_updates_existing_branch(self):
        old = inbox_pr_guard.render_marker(
            "update",
            ["backlog_issue:MYPL-3@2026-10-01T00:00:00Z"],
        )
        plan = inbox_pr_guard.build_plan(
            compare_result(),
            {"new": [], "update": [open_pr(7, old, "inbox-update-existing")]},
        )
        self.assertEqual(plan["update"]["action"], "update")
        self.assertEqual(plan["update"]["reason"], "fingerprint_changed")
        self.assertEqual(plan["update"]["pr"]["headRefName"], "inbox-update-existing")

    def test_missing_marker_updates_existing_pr(self):
        plan = inbox_pr_guard.build_plan(
            compare_result(),
            {"new": [open_pr(3, "本文だけ")], "update": []},
        )
        self.assertEqual(plan["new"]["action"], "update")
        self.assertEqual(plan["new"]["reason"], "marker_missing")

    def test_no_candidates_skips_even_if_pr_is_open(self):
        plan = inbox_pr_guard.build_plan(
            {"candidates": [], "missing_from_cache": []},
            {"new": [open_pr(9, "old")], "update": []},
        )
        self.assertEqual(plan["new"]["action"], "skip")
        self.assertEqual(plan["new"]["reason"], "no_candidates")
        self.assertEqual(plan["new"]["pr"]["number"], 9)
        self.assertEqual(plan["update"]["action"], "skip")
        self.assertIsNone(plan["update"]["pr"])

    def test_multiple_open_prs_stop(self):
        with self.assertRaises(inbox_pr_guard.GuardError) as caught:
            inbox_pr_guard.decide(
                "new",
                [candidate("github_issue", "owner/repo#1", "2026-10-01T00:00:00Z")],
                [open_pr(1, ""), open_pr(2, "")],
            )
        self.assertIn("複数", str(caught.exception))
        self.assertIn("1", str(caught.exception))
        self.assertIn("2", str(caught.exception))

    def test_conflicting_markers_stop(self):
        body = (
            inbox_pr_guard.render_marker(
                "new", ["github_issue:owner/repo#1@2026-10-01T00:00:00Z"]
            )
            + "\n"
            + inbox_pr_guard.render_marker(
                "new", ["github_issue:owner/repo#2@2026-10-02T00:00:00Z"]
            )
        )
        with self.assertRaises(inbox_pr_guard.GuardError):
            inbox_pr_guard.marker_identities(body, "new")

    def test_missing_label_is_no_open_pr(self):
        self.assertTrue(
            inbox_pr_guard.is_missing_label("could not find label 'inbox-new'")
        )
        self.assertTrue(
            inbox_pr_guard.is_missing_label("the label inbox-new is not found")
        )
        self.assertFalse(
            inbox_pr_guard.is_missing_label("HTTP 404: Not Found (https://api.github.com/repos/a/b)")
        )

    def test_cli_uses_compare_json_and_gh_lists(self):
        created = inbox_pr_guard.build_plan(compare_result(), {"new": [], "update": []})
        calls: list[list[str]] = []

        def runner(args, cwd):
            calls.append(list(args))
            if args[:2] == ["repo", "view"]:
                return completed("owner/task_management\n")
            label = args[args.index("--label") + 1]
            if label == "inbox-new":
                return completed(json.dumps([open_pr(4, created["new"]["body_marker"])]))
            if label == "inbox-update":
                return completed("", stderr="could not find label 'inbox-update'", returncode=1)
            raise AssertionError(args)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "compare.json"
            path.write_text(json.dumps(compare_result()), encoding="utf-8")
            stdout = sys.stdout
            try:
                buffer = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
                sys.stdout = buffer
                code = inbox_pr_guard.main(
                    ["--compare-json", str(path), "--vault", temp],
                    runner=runner,
                )
                buffer.seek(0)
                plan = json.loads(buffer.read())
            finally:
                sys.stdout = stdout
                buffer.close()

        self.assertEqual(code, 0)
        self.assertEqual(plan["new"]["action"], "skip")
        self.assertEqual(plan["new"]["reason"], "unchanged")
        self.assertEqual(plan["update"]["action"], "create")
        self.assertEqual(calls[0][0], "repo")
        self.assertIn("--label", calls[1])
        self.assertNotIn("GH_TOKEN", " ".join(calls[0]))

    def test_gh_failure_is_not_treated_as_no_pr(self):
        def runner(args, cwd):
            if args[:2] == ["repo", "view"]:
                return completed("owner/task_management\n")
            return completed("", stderr="HTTP 401: Bad credentials", returncode=1)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "compare.json"
            path.write_text(json.dumps({"candidates": [], "missing_from_cache": []}), encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                inbox_pr_guard.main(
                    ["--compare-json", str(path), "--vault", temp],
                    runner=runner,
                )
        self.assertIn("open PR の取得に失敗しました", str(caught.exception))

    def test_split_matches_live_compare(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp)
            github = vault / "sources/github"
            github.mkdir(parents=True)
            (github / "assigned-issues.json").write_text(
                json.dumps(
                    [
                        {
                            "sourceType": "github_issue",
                            "sourceId": "owner/repo#1",
                            "sourceUrl": "https://github.com/owner/repo/issues/1",
                            "sourceUpdatedAt": "2026-10-01T00:00:00Z",
                            "title": "新規",
                            "state": "open",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (github / "my-prs.json").write_text("[]", encoding="utf-8")
            (github / "review-requests.json").write_text("[]", encoding="utf-8")
            backlog = vault / "sources/backlog"
            backlog.mkdir()
            (backlog / "assigned-issues.json").write_text("[]", encoding="utf-8")

            result = compare_inbox.compare(vault, ["github", "backlog"])
            plan = inbox_pr_guard.build_plan(result, {"new": [], "update": []})

        self.assertEqual(plan["new"]["action"], "create")
        self.assertEqual(
            plan["new"]["identities"],
            ["github_issue:owner/repo#1@2026-10-01T00:00:00Z"],
        )
        self.assertEqual(plan["update"]["action"], "skip")
        markdown = compare_inbox.format_markdown(result)
        self.assertIn("github_issue** | `owner/repo#1`", markdown)


if __name__ == "__main__":
    unittest.main()
