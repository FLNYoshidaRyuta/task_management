"""tasks/items 本文の見出しを揃える。

トップレベルは ## 概要 / ## やったこと / ## 残りのやること のみ。
各セクション内の見出しは ### 以上に正規化する。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SECTION_NAMES = ("概要", "やったこと", "残りのやること")
FULL_LINE_BOLD = re.compile(r"^\*\*(.+)\*\*\s*$")


def parse_sections(body: str) -> dict[str, str]:
    body = body.replace("\r\n", "\n")
    result = {name: "" for name in SECTION_NAMES}
    for name in SECTION_NAMES:
        m = re.search(rf"^## {name}\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL | re.MULTILINE)
        if m:
            result[name] = m.group(1).strip()
    return result


def normalize_inner(content: str) -> str:
    if not content.strip():
        return ""
    lines: list[str] = []
    for line in content.splitlines():
        if re.match(r"^#{1,2}\s+\S", line):
            title = re.sub(r"^#+\s*", "", line).strip()
            if title in SECTION_NAMES:
                continue
            lines.append(f"### {title}")
            continue
        bold = FULL_LINE_BOLD.match(line.strip())
        if bold and len(line.strip()) <= 120:
            lines.append(f"### {bold.group(1).strip()}")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def render_body(sections: dict[str, str]) -> str:
    parts: list[str] = []
    for name in SECTION_NAMES:
        parts.append(f"## {name}\n")
        content = sections.get(name, "").strip()
        if content:
            parts.append(content)
            parts.append("")
        else:
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changed: list[str] = []

    for path in sorted(ITEMS.rglob("*.md")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = FM_RE.match(text)
        if not m:
            continue
        data = yaml.safe_load(m.group(1)) or {}
        sections = parse_sections(m.group(2))
        new_sections = {name: normalize_inner(sections[name]) for name in SECTION_NAMES}
        new_body = render_body(new_sections)
        old_body = m.group(2)
        if new_body != old_body:
            rel = path.relative_to(VAULT).as_posix()
            changed.append(rel)
            if not args.dry_run:
                header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
                path.write_text(f"---\n{header}---\n{new_body}", encoding="utf-8")

    for rel in changed:
        print(rel)
    print(f"changed: {len(changed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
