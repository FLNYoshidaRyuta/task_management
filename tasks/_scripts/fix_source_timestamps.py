"""移行後の github/backlog updated_at を ISO Z 文字列に直す。"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from compare_inbox import as_text

ITEMS = Path(__file__).resolve().parents[2] / "tasks" / "items"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def normalize_field(value):
    text = as_text(value)
    return text if text else ""


def main() -> None:
    for path in ITEMS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = FM_RE.match(text.replace("\r\n", "\n"))
        if not match:
            continue
        data = yaml.safe_load(match.group(1)) or {}
        for key in ("github_updated_at", "backlog_updated_at"):
            if key in data:
                data[key] = normalize_field(data.get(key))
        for key in ("start", "end"):
            if data.get(key) is None:
                data[key] = ""
        header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        path.write_text(f"---\n{header}---\n{match.group(2)}", encoding="utf-8")


if __name__ == "__main__":
    main()
