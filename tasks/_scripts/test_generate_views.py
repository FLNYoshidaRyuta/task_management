import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_views


class RelatedViewTest(unittest.TestCase):
    def setUp(self):
        self.vault = Path(tempfile.gettempdir()) / "related-view-test"
        self.vault.mkdir(parents=True, exist_ok=True)

    def task(self, rel_path: str, title: str, **extra):
        path = self.vault / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "---",
            f"title: {title}",
            "project: サンプル",
            "status: todo",
        ]
        for key, value in extra.items():
            if key in ("depends_on", "related") and isinstance(value, list):
                if value:
                    lines.append(f"{key}:")
                    lines.extend(f"  - {item}" for item in value)
                else:
                    lines.append(f"{key}: []")
            else:
                lines.append(f"{key}: {value}")
        lines.extend(["---", ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        return {
            "title": title,
            "_path": path,
            **extra,
        }

    def test_bidirectional_related_draws_single_edge(self):
        link_a = (
            "[[tasks/items/サンプル/B|B]]"
        )
        link_b = (
            "[[tasks/items/サンプル/A|A]]"
        )
        tasks = [
            self.task(
                "tasks/items/サンプル/A.md",
                "A",
                related=[link_a],
            ),
            self.task(
                "tasks/items/サンプル/B.md",
                "B",
                related=[link_b],
            ),
        ]

        text = generate_views.render_related(tasks, self.vault)

        self.assertIn("T0 --- T1", text)
        self.assertNotIn("## 不整合", text)

    def test_one_sided_related_draws_edge_and_reports_inconsistency(self):
        link = "[[tasks/items/サンプル/B|B]]"
        tasks = [
            self.task("tasks/items/サンプル/A.md", "A", related=[link]),
            self.task("tasks/items/サンプル/B.md", "B"),
        ]

        text = generate_views.render_related(tasks, self.vault)

        self.assertIn("T0 --- T1", text)
        self.assertIn("## 不整合", text)
        self.assertIn("片側だけ", text)
        self.assertIn("tasks/items/サンプル/A", text)

    def test_self_link_and_unresolvable_are_reported_without_edge(self):
        tasks = [
            self.task(
                "tasks/items/サンプル/A.md",
                "A",
                related=[
                    "[[tasks/items/サンプル/A|A]]",
                    "[[tasks/items/サンプル/Missing|Missing]]",
                ],
            ),
        ]

        text = generate_views.render_related(tasks, self.vault)

        self.assertNotIn("```mermaid", text)
        self.assertIn("自分自身", text)
        self.assertIn("解決できないリンク", text)

    def test_tasks_without_related_are_not_nodes(self):
        tasks = [
            self.task("tasks/items/サンプル/A.md", "A"),
            self.task("tasks/items/サンプル/B.md", "B"),
        ]

        text = generate_views.render_related(tasks, self.vault)

        self.assertEqual(text.strip(), "# 関連図\n\n関連タスクはありません。")

    def test_depends_on_does_not_appear_in_related_view(self):
        tasks = [
            self.task(
                "tasks/items/サンプル/A.md",
                "A",
                depends_on=["[[tasks/items/サンプル/B|B]]"],
            ),
            self.task("tasks/items/サンプル/B.md", "B"),
        ]

        text = generate_views.render_related(tasks, self.vault)

        self.assertEqual(text.strip(), "# 関連図\n\n関連タスクはありません。")


if __name__ == "__main__":
    unittest.main()
