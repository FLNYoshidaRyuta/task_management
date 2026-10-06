"""gh の JSON を、sourceId を持つ取得キャッシュへ整形する。"""

from __future__ import annotations

import json
import sys


def normalize(items: list, source_type: str) -> list:
    result = []

    for item in items:
        repository = item.get("repository")
        name = repository.get("nameWithOwner") if isinstance(repository, dict) else None
        number = item.get("number")

        if not name or number is None:
            raise SystemExit("GitHub item is missing repository.nameWithOwner or number")

        normalized = {
            "sourceType": source_type,
            "sourceId": f"{name}#{number}",
            "sourceUrl": item.get("url"),
            "sourceUpdatedAt": item.get("updatedAt"),
            "title": item.get("title"),
            "state": item.get("state"),
        }

        for key in (
            "number",
            "body",
            "repository",
            "labels",
            "assignees",
            "author",
            "isDraft",
            "createdAt",
            "updatedAt",
        ):
            if key in item:
                normalized[key] = item[key]

        result.append(normalized)

    return result


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: normalize_github.py <source_type> <in_path> <out_path>")

    source_type = sys.argv[1]
    in_path = sys.argv[2]
    out_path = sys.argv[3]

    if source_type not in ("github_issue", "github_pr"):
        raise SystemExit(f"unsupported source_type: {source_type}")

    with open(in_path, encoding="utf-8") as handle:
        raw = handle.read().strip()

    items = json.loads(raw) if raw else []

    if isinstance(items, dict):
        items = [items]

    result = normalize(items, source_type)

    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
