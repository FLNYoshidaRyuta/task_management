import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_routines
import generate_views


TREE = """# タスク

## タスクツリー

### サンプル

- [[tasks/items/サンプル/Github Issue対応|GitHub Issue対応]]

## ガントチャート

![[ガントチャート.md]]

## 依存関係図

![[依存関係図.md]]

## タスクリスト

![[タスクビュー.base#現役]]
"""

WEEKLY = """---
id: weekly-review
title: 週次レビュー
project: 個人
recurrence: weekly
weekday: friday
priority: Mid
estimate: 30m
generate_before_days: 7
---

## 完了条件

- 今週の未完了タスクを確認
- 来週の予定を整理
"""

BILLING = """---
id: monthly-billing
title: 月次請求処理
project: 個人
recurrence: monthly
day: 1
priority: Mid
estimate: 2h
generate_before_days: 40
children:
  - id: check-usage
    title: 利用実績確認
    estimate: 30m
  - id: create-invoice
    title: 請求データ作成
    estimate: 1h
    depends_on:
      - check-usage
  - id: request-review
    title: 確認依頼
    estimate: 15m
    depends_on:
      - 請求データ作成
---

## 完了条件

- 請求まで完了している
"""


class GenerateRoutinesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tasks_dir = Path(self.tmp.name) / "tasks"
        (self.tasks_dir / "routines").mkdir(parents=True)
        (self.tasks_dir / "items").mkdir()
        (self.tasks_dir / "_タスク.md").write_text(TREE, encoding="utf-8", newline="\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write_routine(self, name, text):
        path = self.tasks_dir / "routines" / name
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def test_weekly_creates_next_friday_only(self):
        self.write_routine("weekly-review.md", WEEKLY)

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        created = list((self.tasks_dir / "items" / "routine").glob("*.md"))
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].name, "2026-10-09_週次レビュー.md")
        self.assertEqual(result.errors, [])

        text = created[0].read_text(encoding="utf-8")
        self.assertEqual(
            text,
            """---
title: 週次レビュー
project: 個人
status: todo
start: 2026-10-09
end: 2026-10-09
priority: Mid
estimate: 30m
parent:
depends_on: []

source_type: routine
source_id: weekly-review
routine_date: 2026-10-09
---

## 完了条件

- 今週の未完了タスクを確認
- 来週の予定を整理
""",
        )
        data, body = generate_routines.read_document(created[0])
        self.assertEqual(data["source_type"], "routine")
        self.assertEqual(data["source_id"], "weekly-review")
        self.assertEqual(generate_routines.as_date_str(data["routine_date"]), "2026-10-09")
        self.assertIn("来週の予定を整理", body)

        tree = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")
        self.assertIn("### サンプル", tree)
        self.assertIn("### 個人", tree)
        self.assertIn(
            "- [[tasks/items/routine/2026-10-09_週次レビュー|週次レビュー]]",
            tree,
        )
        self.assertLess(tree.index("### サンプル"), tree.index("### 個人"))
        self.assertLess(tree.index("### 個人"), tree.index("## ガントチャート"))
        self.assertIn("![[ガントチャート.md]]", tree)

    def test_second_run_keeps_completion_and_tree(self):
        self.write_routine("weekly-review.md", WEEKLY)
        generate_routines.generate(self.tasks_dir, date(2026, 10, 6))
        task = self.tasks_dir / "items" / "routine" / "2026-10-09_週次レビュー.md"
        task.write_text(
            task.read_text(encoding="utf-8").replace("status: todo", "status: done"),
            encoding="utf-8",
            newline="\n",
        )
        before = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertEqual(result.created, [])
        self.assertIn("status: done", task.read_text(encoding="utf-8"))
        self.assertEqual((self.tasks_dir / "_タスク.md").read_text(encoding="utf-8"), before)

    def test_dry_run_writes_nothing(self):
        self.write_routine("weekly-review.md", WEEKLY)

        result = generate_routines.generate(
            self.tasks_dir,
            date(2026, 10, 6),
            dry_run=True,
        )

        self.assertEqual(len(result.created), 1)
        self.assertEqual(list((self.tasks_dir / "items").rglob("*.md")), [])
        self.assertNotIn("週次レビュー", (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8"))

    def test_daily_window(self):
        self.write_routine(
            "daily-note.md",
            """---
id: daily-note
title: 日次メモ
project: 個人
recurrence: daily
generate_before_days: 2
---
""",
        )

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))
        names = {path.name for path in result.created}

        self.assertEqual(
            names,
            {
                "2026-10-06_日次メモ.md",
                "2026-10-07_日次メモ.md",
                "2026-10-08_日次メモ.md",
            },
        )

    def test_weekdays_skip_weekend(self):
        self.write_routine(
            "weekday-check.md",
            """---
id: weekday-check
title: 平日確認
project: 個人
recurrence: weekdays
generate_before_days: 3
---
""",
        )

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 9))
        names = {path.name for path in result.created}

        self.assertEqual(
            names,
            {
                "2026-10-09_平日確認.md",
                "2026-10-12_平日確認.md",
            },
        )

    def test_monthly_day_uses_month_end(self):
        self.write_routine(
            "month-end.md",
            """---
id: month-end
title: 月末締め
project: 個人
recurrence: monthly
day: 31
generate_before_days: 27
---
""",
        )

        result = generate_routines.generate(self.tasks_dir, date(2026, 2, 1))

        self.assertEqual(
            {path.name for path in result.created},
            {"2026-02-28_月末締め.md"},
        )

    def test_children_parent_and_dependencies(self):
        self.write_routine("monthly-billing.md", BILLING)

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertEqual(result.errors, [])
        parent = self.tasks_dir / "items" / "routine" / "2026-11-01_月次請求処理.md"
        check = self.tasks_dir / "items" / "routine" / "2026-11-01_月次請求処理_利用実績確認.md"
        invoice = self.tasks_dir / "items" / "routine" / "2026-11-01_月次請求処理_請求データ作成.md"
        review = self.tasks_dir / "items" / "routine" / "2026-11-01_月次請求処理_確認依頼.md"
        self.assertTrue(parent.exists())
        self.assertTrue(check.exists())
        self.assertTrue(invoice.exists())
        self.assertTrue(review.exists())

        invoice_data, _body = generate_routines.read_document(invoice)
        self.assertEqual(invoice_data["source_id"], "monthly-billing/create-invoice")
        self.assertEqual(
            invoice_data["parent"],
            "[[tasks/items/routine/2026-11-01_月次請求処理|月次請求処理]]",
        )
        self.assertEqual(
            invoice_data["depends_on"],
            ["[[tasks/items/routine/2026-11-01_月次請求処理_利用実績確認|利用実績確認]]"],
        )
        self.assertIsNone(invoice_data["priority"])
        self.assertEqual(invoice_data["estimate"], "1h")
        self.assertEqual(invoice_data["project"], "個人")

        review_data, _body = generate_routines.read_document(review)
        self.assertEqual(
            review_data["depends_on"],
            ["[[tasks/items/routine/2026-11-01_月次請求処理_請求データ作成|請求データ作成]]"],
        )

        tree = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")
        parent_at = tree.index("[[tasks/items/routine/2026-11-01_月次請求処理|月次請求処理]]")
        check_at = tree.index("[[tasks/items/routine/2026-11-01_月次請求処理_利用実績確認|利用実績確認]]")
        self.assertLess(parent_at, check_at)
        self.assertIn("\n  - [[tasks/items/routine/2026-11-01_月次請求処理_利用実績確認|利用実績確認]]", tree)

    def test_new_child_is_added_under_existing_parent(self):
        self.write_routine(
            "monthly-billing.md",
            """---
id: monthly-billing
title: 月次請求処理
project: 個人
recurrence: monthly
day: 1
generate_before_days: 40
children:
  - id: check-usage
    title: 利用実績確認
---
""",
        )
        generate_routines.generate(self.tasks_dir, date(2026, 10, 6))
        self.write_routine("monthly-billing.md", BILLING)

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        names = {path.name for path in result.created}
        self.assertNotIn("2026-11-01_月次請求処理.md", names)
        self.assertIn("2026-11-01_月次請求処理_請求データ作成.md", names)
        tree = (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8")
        self.assertEqual(tree.count("2026-11-01_月次請求処理|月次請求処理"), 1)
        self.assertIn("2026-11-01_月次請求処理_確認依頼", tree)

    def test_invalid_definition_writes_nothing(self):
        self.write_routine("weekly-review.md", WEEKLY)
        self.write_routine(
            "broken.md",
            """---
id: broken
title: 壊れた定義
project: 個人
recurrence: weekly
generate_before_days: 7
---
""",
        )

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertTrue(result.errors)
        self.assertEqual(result.created, [])
        self.assertEqual(list((self.tasks_dir / "items").rglob("*.md")), [])
        self.assertNotIn("### 個人", (self.tasks_dir / "_タスク.md").read_text(encoding="utf-8"))

    def test_filename_must_match_id(self):
        self.write_routine("different-name.md", WEEKLY)

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertTrue(any("ファイル名は id と一致" in error for error in result.errors))
        self.assertEqual(result.created, [])

    def test_disabled_routine_is_skipped(self):
        text = WEEKLY.replace("priority: Mid", "priority: Mid\nenabled: false")
        self.write_routine("weekly-review.md", text)

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertEqual(result.created, [])
        self.assertEqual(result.disabled, ["weekly-review"])

    def test_moved_task_is_not_duplicated(self):
        self.write_routine("weekly-review.md", WEEKLY)
        generate_routines.generate(self.tasks_dir, date(2026, 10, 6))
        source = self.tasks_dir / "items" / "routine" / "2026-10-09_週次レビュー.md"
        target_dir = self.tasks_dir / "items" / "個人"
        target_dir.mkdir()
        target = target_dir / source.name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        source.unlink()

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertEqual(result.created, [])
        self.assertEqual(list((self.tasks_dir / "items").rglob("*.md")), [target])

    def test_cycle_is_rejected(self):
        self.write_routine(
            "cycle.md",
            """---
id: cycle
title: 循環
project: 個人
recurrence: daily
generate_before_days: 0
children:
  - id: a
    title: A
    depends_on:
      - b
  - id: b
    title: B
    depends_on:
      - a
---
""",
        )

        result = generate_routines.generate(self.tasks_dir, date(2026, 10, 6))

        self.assertTrue(any("循環" in error for error in result.errors))
        self.assertEqual(result.created, [])


class DependencyViewTest(unittest.TestCase):
    def test_same_title_uses_path(self):
        vault = Path(tempfile.gettempdir()) / "routine-view-test"
        first = vault / "tasks" / "items" / "routine" / "2026-10-09_週次レビュー.md"
        second = vault / "tasks" / "items" / "routine" / "2026-10-16_週次レビュー.md"
        tasks = [
            {
                "title": "週次レビュー",
                "_path": first,
                "depends_on": [],
            },
            {
                "title": "週次レビュー",
                "_path": second,
                "depends_on": [
                    "[[tasks/items/routine/2026-10-09_週次レビュー|週次レビュー]]"
                ],
            },
        ]

        text = generate_views.render_dependency(tasks, vault)

        self.assertIn('T0["週次レビュー"]', text)
        self.assertIn('T1["週次レビュー"]', text)
        self.assertIn("T0 --> T1", text)

    def test_unique_title_still_resolves(self):
        vault = Path(tempfile.gettempdir()) / "routine-view-test-unique"
        tasks = [
            {
                "title": "先行",
                "_path": vault / "tasks" / "items" / "先行.md",
                "depends_on": [],
            },
            {
                "title": "後続",
                "_path": vault / "tasks" / "items" / "後続.md",
                "depends_on": ["先行"],
            },
        ]

        text = generate_views.render_dependency(tasks, vault)

        self.assertIn("T0 --> T1", text)


class CheckedInRoutineTest(unittest.TestCase):
    def test_routines_dir_loads_without_errors(self):
        routines_dir = Path(__file__).resolve().parents[1] / "routines"
        routines, errors = generate_routines.load_routines(routines_dir)

        self.assertEqual(errors, [])
        self.assertIsInstance(routines, list)


if __name__ == "__main__":
    unittest.main()
