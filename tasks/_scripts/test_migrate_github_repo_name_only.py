import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import migrate_github_repo_name_only


class MigrateGithubRepoNameOnlyTest(unittest.TestCase):
    def test_strips_owner(self):
        text = """---
title: sample
github_type:
  - github_issue
github_repo: FutureLinkNetwork/mypl_pro
github_id: Issue#1
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1
---
"""
        new_text, error = migrate_github_repo_name_only.migrate_text(text)
        self.assertIsNone(error)
        self.assertIn("github_repo: mypl_pro", new_text)
        self.assertNotIn("github_repo: FutureLinkNetwork/mypl_pro", new_text)

    def test_skips_name_only(self):
        text = """---
github_repo: mypl_pro
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1
---
"""
        new_text, error = migrate_github_repo_name_only.migrate_text(text)
        self.assertIsNone(error)
        self.assertEqual(new_text, text)


if __name__ == "__main__":
    unittest.main()
