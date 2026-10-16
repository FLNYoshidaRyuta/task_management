"""誤って ## やったこと 内に入った ### 残りのやること などを直す。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from normalize_task_headings import parse_sections, render_body

VAULT = Path(__file__).resolve().parents[2]
ITEMS = VAULT / "tasks" / "items"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SECTION_NAMES = ("概要", "やったこと", "残りのやること")
ORPHAN_REMAINING = re.compile(
    r"^###\s+残りのやること\s*\n(.*)$", re.DOTALL | re.MULTILINE
)


def repair_sections(sections: dict[str, str]) -> dict[str, str]:
    out = dict(sections)
    done = out.get("やったこと", "").strip()
    remaining = out.get("残りのやること", "").strip()

    m = ORPHAN_REMAINING.fullmatch(done)
    if m:
        orphan_body = m.group(1).strip()
        out["やったこと"] = ""
        if not remaining:
            out["残りのやること"] = orphan_body
        elif remaining == orphan_body:
            pass
        else:
            out["残りのやること"] = remaining

    if out.get("やったこと", "").strip() in ("### 残りのやること", ""):
        if out["やったこと"].strip() == "### 残りのやること":
            out["やったこと"] = ""

    # やったことと残りが同一なら、未完了想定で残りだけ残す（やったことが空のとき）
    if (
        out.get("やったこと", "").strip()
        and out.get("やったこと", "").strip() == out.get("残りのやること", "").strip()
    ):
        out["やったこと"] = ""

    return out


def main() -> int:
    changed: list[str] = []
    for path in sorted(ITEMS.rglob("*.md")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = FM_RE.match(text)
        if not m:
            continue
        data = yaml.safe_load(m.group(1)) or {}
        sections = parse_sections(m.group(2))
        repaired = repair_sections(sections)
        new_body = render_body(repaired)
        if new_body != m.group(2):
            header = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
            path.write_text(f"---\n{header}---\n{new_body}", encoding="utf-8")
            changed.append(path.relative_to(VAULT).as_posix())
    for rel in changed:
        print(rel)
    print(f"changed: {len(changed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
