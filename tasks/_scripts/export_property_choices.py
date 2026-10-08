"""tasks/_config/property-choices.json を task_properties の定義から書き出す。"""

from __future__ import annotations

import json
from pathlib import Path

from task_properties import PROPERTY_CHOICES

TASKS_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = TASKS_DIR / "_config" / "property-choices.json"


def main() -> None:
    payload = {key: list(choices) for key, choices in PROPERTY_CHOICES.items()}
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {OUT_PATH.relative_to(TASKS_DIR.parent)}")


if __name__ == "__main__":
    main()
