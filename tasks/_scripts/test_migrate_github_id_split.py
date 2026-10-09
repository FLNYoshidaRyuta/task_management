import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import migrate_github_id_split


class MigrateGithubIdSplitTest(unittest.TestCase):
    def test_migrates_legacy_github_id(self):
        text = """---
title: sample
status:
  - todo
github_type:
  - github_issue
github_id: org/repo#42
github_url: https://github.com/org/repo/issues/42
---

本文はそのまま
"""
        new_text, error = migrate_github_id_split.migrate_text(text)
        self.assertIsNone(error)
        self.assertIn("github_repo: repo", new_text)
        self.assertIn("github_id: Issue#42", new_text)
        self.assertNotIn("org/repo#42", new_text)
        self.assertIn("本文はそのまま", new_text)

    def test_skips_already_migrated(self):
        text = """---
title: sample
github_type:
  - github_pr
github_repo: org/repo
github_id: PR#1
github_url: https://github.com/org/repo/pull/1
---
"""
        new_text, error = migrate_github_id_split.migrate_text(text)
        self.assertIsNone(error)
        self.assertEqual(new_text, text)

    def test_refuses_url_mismatch(self):
        text = """---
title: sample
github_type:
  - github_issue
github_id: org/repo#1
github_url: https://github.com/org/repo/issues/2
---
"""
        new_text, error = migrate_github_id_split.migrate_text(text)
        self.assertIsNotNone(error)
        self.assertEqual(new_text, text)


if __name__ == "__main__":
    unittest.main()
