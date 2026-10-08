import unittest

from task_properties import single_choice


class SingleChoiceTest(unittest.TestCase):
    def test_empty_values(self):
        self.assertEqual(single_choice(None), "")
        self.assertEqual(single_choice(""), "")
        self.assertEqual(single_choice([]), "")

    def test_string_value(self):
        self.assertEqual(single_choice("todo"), "todo")
        self.assertEqual(single_choice("  done  "), "done")

    def test_single_item_list(self):
        self.assertEqual(single_choice(["in_progress"]), "in_progress")

    def test_multi_item_list_returns_empty(self):
        self.assertEqual(single_choice(["todo", "done"]), "")


if __name__ == "__main__":
    unittest.main()
