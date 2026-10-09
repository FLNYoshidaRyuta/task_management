import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_task_properties


class ValidateTaskPropertiesTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.items = self.root / "tasks" / "items" / "sample"
        self.items.mkdir(parents=True)

    def write_task(self, name: str, body: str):
        path = self.items / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_empty_lists_are_valid(self):
        path = self.write_task(
            "ok.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status: []",
                    "priority: []",
                    "source_type: []",
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_single_choice_values_are_valid(self):
        path = self.write_task(
            "ok.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority:",
                    "  - High",
                    "github_type:",
                    "  - github_issue",
                    "github_id: org/repo#1",
                    "github_url: https://github.com/org/repo/issues/1",
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_string_status_is_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status: todo",
                    "priority: []",
                    "source_type: []",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("status はリスト" in item for item in errors))

    def test_two_status_values_are_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "  - done",
                    "priority: []",
                    "source_type: []",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("0件または1件" in item for item in errors))

    def test_new_dual_pointers_are_valid(self):
        path = self.write_task(
            "dual.md",
            "\n".join(
                [
                    "---",
                    "title: dual",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "github_type:",
                    "  - github_issue",
                    "github_id: org/repo#1",
                    "github_url: https://github.com/org/repo/issues/1",
                    "backlog_id: MYPL-1",
                    "backlog_url: https://example.test/view/MYPL-1",
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_github_id_without_type_is_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: bad",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "github_id: org/repo#1",
                    "github_url: https://github.com/org/repo/issues/1",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("github_type" in item for item in errors))

    def test_focus_date_absent_is_valid(self):
        path = self.write_task(
            "ok.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_focus_date_empty_is_valid(self):
        path = self.write_task(
            "ok.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    'focus_date: ""',
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_focus_date_iso_is_valid(self):
        path = self.write_task(
            "ok.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "focus_date: 2026-10-09",
                    "---",
                    "",
                ]
            ),
        )
        self.assertEqual(validate_task_properties.validate_file(path), [])

    def test_focus_date_garbage_string_is_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "focus_date: today",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("focus_date" in item for item in errors))

    def test_focus_date_list_is_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority: []",
                    "source_type: []",
                    "focus_date:",
                    "  - 2026-10-09",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("focus_date" in item for item in errors))

    def test_unknown_priority_is_invalid(self):
        path = self.write_task(
            "bad.md",
            "\n".join(
                [
                    "---",
                    "title: sample",
                    "status:",
                    "  - todo",
                    "priority:",
                    "  - Urgent",
                    "source_type: []",
                    "---",
                    "",
                ]
            ),
        )
        errors = validate_task_properties.validate_file(path)
        self.assertTrue(any("priority の値が不正" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
