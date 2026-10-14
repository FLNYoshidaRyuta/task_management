import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import runtime_env


class RuntimeEnvTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        self.keys = ("GH_TOKEN", "BACKLOG_API_KEY", "BACKLOG_BASE_URL")
        self.saved = {key: os.environ.get(key) for key in self.keys}
        for key in self.keys:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def test_existing_environment_wins_over_dotenv(self):
        os.environ["GH_TOKEN"] = "runtime-secret"
        os.environ["BACKLOG_API_KEY"] = "runtime-key"
        (self.vault / ".env").write_text(
            "GH_TOKEN=from-file\nBACKLOG_API_KEY=file-key\nBACKLOG_BASE_URL=https://example.backlog.jp\n",
            encoding="utf-8",
        )

        runtime_env.load_env_file(self.vault / ".env")

        self.assertEqual(os.environ["GH_TOKEN"], "runtime-secret")
        self.assertEqual(os.environ["BACKLOG_API_KEY"], "runtime-key")
        self.assertEqual(os.environ["BACKLOG_BASE_URL"], "https://example.backlog.jp")

    def test_dotenv_fills_missing_and_strips_quotes(self):
        (self.vault / ".env").write_text(
            "\n# comment\nGH_TOKEN='from-file'\nBACKLOG_API_KEY=\"file-key\"\n",
            encoding="utf-8",
        )

        runtime_env.load_env_file(self.vault / ".env")

        self.assertEqual(os.environ["GH_TOKEN"], "from-file")
        self.assertEqual(os.environ["BACKLOG_API_KEY"], "file-key")

    def test_blank_environment_value_is_filled_from_dotenv(self):
        os.environ["GH_TOKEN"] = "   "
        (self.vault / ".env").write_text("GH_TOKEN=from-file\n", encoding="utf-8")

        runtime_env.load_env_file(self.vault / ".env")

        self.assertEqual(os.environ["GH_TOKEN"], "from-file")

    def test_gh_env_drops_blank_token(self):
        os.environ["GH_TOKEN"] = "  "
        env = runtime_env.gh_env()
        self.assertNotIn("GH_TOKEN", env)

    def test_gh_env_keeps_runtime_token(self):
        os.environ["GH_TOKEN"] = " runtime-secret "
        env = runtime_env.gh_env()
        self.assertEqual(env["GH_TOKEN"], "runtime-secret")


if __name__ == "__main__":
    unittest.main()
