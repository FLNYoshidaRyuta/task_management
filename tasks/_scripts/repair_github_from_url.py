from __future__ import annotations

import re
from pathlib import Path

import yaml

from task_source_links import github_id_from_url

ITEMS = Path(__file__).resolve().parents[2] / "tasks" / "items"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def main() -> None:
    for path in ITEMS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        m = FM.match(text.replace("\r\n", "\n"))
        if not m:
            continue
        data = yaml.safe_load(m.group(1)) or {}
        url = (data.get("github_url") or "").strip()
        gid = (data.get("github_id") or "").strip()
        if url and not gid:
            parsed = github_id_from_url(url)
            if parsed:
                data["github_type"] = [parsed[0]]
                data["github_id"] = parsed[1]
        header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        path.write_text(f"---\n{header}---\n{m.group(2)}", encoding="utf-8")


if __name__ == "__main__":
    main()
