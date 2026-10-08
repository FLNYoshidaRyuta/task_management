import unittest

from task_source_links import (
    github_ids_from_text,
    task_source_identities,
)


class TaskSourceLinksTest(unittest.TestCase):
    def test_dual_format_identities(self):
        data = {
            "github_type": ["github_issue"],
            "github_id": "org/repo#1",
            "backlog_id": "MYPL-2",
            "source_type": [],
        }
        identities = task_source_identities(data)
        self.assertEqual(
            set(identities),
            {("github_issue", "org/repo#1"), ("backlog_issue", "MYPL-2")},
        )

    def test_github_url_in_backlog_text(self):
        text = "see https://github.com/FutureLinkNetwork/agent-dev/issues/467"
        found = github_ids_from_text(text)
        self.assertEqual(
            found,
            [("github_issue", "FutureLinkNetwork/agent-dev#467")],
        )


if __name__ == "__main__":
    unittest.main()
