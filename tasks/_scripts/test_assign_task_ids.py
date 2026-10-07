import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import assign_task_ids


class AssignTaskIdsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="assign-task-id-"))
        self.tasks_dir = self.root / "tasks"
        self.items = self.tasks_dir / "items" / "サンプル"
        self.items.mkdir(parents=True)
        self.config = self.tasks_dir / "_config"
        self.config.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_task(self, name: str, title: str, **extra) -> Path:
        path = self.items / name
        lines = ["---", f"title: {title}", "project: サンプル", "status: todo"]
        for key, value in extra.items():
            lines.append(f"{key}: {value}")
        lines.extend(["---", ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_tree(self, body: str) -> None:
        text = (
            "# タスク\n\n## タスクツリー\n\n"
            + body
            + "\n\n## 依存関係図\n\n![[依存関係図.md]]\n"
        )
        (self.tasks_dir / "_タスク.md").write_text(text, encoding="utf-8")

    def test_assigns_in_tree_order_then_path_order(self):
        b = self.write_task("B.md", "B")
        a = self.write_task("A.md", "A")
        c = self.write_task("C.md", "C")
        self.write_tree(
            "\n".join(
                [
                    f"- [[tasks/items/サンプル/B|B]]",
                    f"- [[tasks/items/サンプル/A|A]]",
                ]
            )
        )

        assigned, next_id = assign_task_ids.assign(self.tasks_dir)

        self.assertEqual(assigned, 3)
        self.assertEqual(next_id, 4)
        self.assertIn("task_id: 1", b.read_text(encoding="utf-8"))
        self.assertIn("task_id: 2", a.read_text(encoding="utf-8"))
        self.assertIn("task_id: 3", c.read_text(encoding="utf-8"))

    def test_second_run_is_idempotent(self):
        self.write_task("A.md", "A")
        self.write_tree("- [[tasks/items/サンプル/A|A]]")

        assign_task_ids.assign(self.tasks_dir)
        first = (self.items / "A.md").read_text(encoding="utf-8")
        tree_first = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")

        assigned, _ = assign_task_ids.assign(self.tasks_dir)

        self.assertEqual(assigned, 0)
        self.assertEqual(first, (self.items / "A.md").read_text(encoding="utf-8"))
        self.assertEqual(tree_first, (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8"))

    def test_existing_id_preserved_and_new_uses_cursor(self):
        self.write_task("A.md", "A", task_id=3)
        self.write_task("B.md", "B")
        (self.config / "task-id.json").write_text(
            json.dumps({"next_id": 10}) + "\n",
            encoding="utf-8",
        )
        self.write_tree(
            "\n".join(
                [
                    "- [[tasks/items/サンプル/A|A]]",
                    "- [[tasks/items/サンプル/B|B]]",
                ]
            )
        )

        assign_task_ids.assign(self.tasks_dir)

        self.assertIn("task_id: 3", (self.items / "A.md").read_text(encoding="utf-8"))
        self.assertIn("task_id: 10", (self.items / "B.md").read_text(encoding="utf-8"))
        config = json.loads((self.config / "task-id.json").read_text(encoding="utf-8"))
        self.assertEqual(config["next_id"], 11)

    def test_deleted_file_number_not_reused(self):
        path = self.write_task("A.md", "A")
        self.write_tree("- [[tasks/items/サンプル/A|A]]")
        assign_task_ids.assign(self.tasks_dir)
        path.unlink()

        self.write_task("B.md", "B")
        self.write_tree("- [[tasks/items/サンプル/B|B]]")
        assign_task_ids.assign(self.tasks_dir)

        self.assertIn("task_id: 2", (self.items / "B.md").read_text(encoding="utf-8"))

    def test_duplicate_id_fails_without_writes(self):
        self.write_task("A.md", "A", task_id=1)
        self.write_task("B.md", "B", task_id=1)
        self.write_tree(
            "\n".join(
                [
                    "- [[tasks/items/サンプル/A|A]]",
                    "- [[tasks/items/サンプル/B|B]]",
                ]
            )
        )

        with self.assertRaises(ValueError):
            assign_task_ids.assign(self.tasks_dir)

    def test_invalid_id_fails_without_writes(self):
        self.write_task("A.md", "A", task_id=0)
        self.write_tree("- [[tasks/items/サンプル/A|A]]")

        with self.assertRaises(ValueError):
            assign_task_ids.assign(self.tasks_dir)

    def test_strikethrough_link_keeps_markup(self):
        path = self.write_task("A.md", "A")
        self.write_tree(f"- ~~[[tasks/items/サンプル/A|A]]~~")

        assign_task_ids.assign(self.tasks_dir)

        tree = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")
        self.assertIn("~~[[tasks/items/サンプル/A|1 A]]~~", tree)

    def test_migrates_legacy_id_field_to_task_id(self):
        path = self.items / "A.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    "id: 7",
                    "title: A",
                    "project: サンプル",
                    "status: todo",
                    "---",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.write_tree("- [[tasks/items/サンプル/A|A]]")

        assign_task_ids.assign(self.tasks_dir)

        text = path.read_text(encoding="utf-8")
        self.assertIn("task_id: 7", text)
        self.assertNotIn("\nid:", text)

    def test_tree_alias_rebuilt_from_title_not_old_alias(self):
        path = self.write_task("A.md", "正しいタイトル", task_id=5)
        self.write_tree("- [[tasks/items/サンプル/A|古い表示名]]")

        assign_task_ids.assign(self.tasks_dir)

        tree = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")
        self.assertIn("[[tasks/items/サンプル/A|5 正しいタイトル]]", tree)


if __name__ == "__main__":
    unittest.main()
