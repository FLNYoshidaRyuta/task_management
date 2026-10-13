"""Inbox でタスク化しないと判断した候補を tasks/_config/inbox-skipped.json に保持する。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from compare_inbox import SOURCE_FILES, merge_candidates, load_json_list

SKIPPED_RELATIVE = Path("tasks") / "_config" / "inbox-skipped.json"
VALID_SOURCE_TYPES = frozenset({"github_issue", "github_pr", "backlog_issue"})


def skipped_config_path(vault: Path) -> Path:
    return vault / SKIPPED_RELATIVE


def parse_identity(text: str) -> tuple[str, str]:
    text = text.strip()
    if ":" not in text:
        raise ValueError(f"invalid identity (expected source_type:source_id): {text}")
    source_type, source_id = text.split(":", 1)
    source_type = source_type.strip()
    source_id = source_id.strip()
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"unsupported source_type: {source_type}")
    if not source_id:
        raise ValueError(f"empty source_id: {text}")
    return source_type, source_id


def format_identity(source_type: str, source_id: str) -> str:
    return f"{source_type}:{source_id}"


def load_skipped_file(vault: Path) -> dict:
    path = skipped_config_path(vault)
    if not path.is_file():
        return {"items": []}

    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return {"items": []}

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"inbox-skipped.json must be an object: {path}")
    items = data.get("items")
    if items is None:
        return {"items": []}
    if not isinstance(items, list):
        raise ValueError(f"inbox-skipped.json items must be a list: {path}")
    return data


def load_skipped_keys(vault: Path) -> frozenset[tuple[str, str]]:
    data = load_skipped_file(vault)
    keys: set[tuple[str, str]] = set()
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        source_type = item.get("source_type")
        source_id = item.get("source_id")
        if isinstance(source_type, str) and isinstance(source_id, str):
            if source_type and source_id:
                keys.add((source_type, source_id))
    return frozenset(keys)


def load_cache_candidates(vault: Path, sources: list[str]) -> dict[tuple[str, str], dict]:
    items: list[dict] = []
    for source in sources:
        for relative in SOURCE_FILES[source]:
            items.extend(load_json_list(vault / relative))
    merged = merge_candidates(items)
    return {(c["source_type"], c["source_id"]): c for c in merged}


def write_skipped_file(vault: Path, data: dict) -> None:
    path = skipped_config_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_skipped(
    vault: Path,
    identities: list[tuple[str, str]],
    sources: list[str],
) -> None:
    cache = load_cache_candidates(vault, sources)
    data = load_skipped_file(vault)
    items: list[dict] = list(data.get("items") or [])
    by_key = {
        (item["source_type"], item["source_id"]): item
        for item in items
        if isinstance(item, dict)
        and isinstance(item.get("source_type"), str)
        and isinstance(item.get("source_id"), str)
    }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for source_type, source_id in identities:
        key = (source_type, source_id)
        candidate = cache.get(key)
        if candidate is None:
            raise ValueError(
                f"not in cache: {format_identity(source_type, source_id)}"
            )

        existing = by_key.get(key)
        if existing is not None:
            existing["title"] = candidate.get("title") or ""
            existing["source_url"] = candidate.get("source_url") or ""
            continue

        entry = {
            "source_type": source_type,
            "source_id": source_id,
            "title": candidate.get("title") or "",
            "source_url": candidate.get("source_url") or "",
            "skipped_at": now,
        }
        items.append(entry)
        by_key[key] = entry

    write_skipped_file(vault, {"items": items})


def remove_skipped(vault: Path, identities: list[tuple[str, str]]) -> None:
    data = load_skipped_file(vault)
    items: list[dict] = list(data.get("items") or [])
    keys_to_remove = set(identities)

    for key in keys_to_remove:
        if not any(
            isinstance(item, dict)
            and item.get("source_type") == key[0]
            and item.get("source_id") == key[1]
            for item in items
        ):
            raise ValueError(f"not in skip list: {format_identity(key[0], key[1])}")

    remaining = [
        item
        for item in items
        if not (
            isinstance(item, dict)
            and (item.get("source_type"), item.get("source_id")) in keys_to_remove
        )
    ]

    write_skipped_file(vault, {"items": remaining})


def format_list_markdown(vault: Path) -> str:
    data = load_skipped_file(vault)
    items = data.get("items") or []
    lines: list[str] = []
    lines.append("## タスク化しないとして保持")
    if not items:
        lines.append("（0件）")
        return "\n".join(lines)

    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        source_type = item.get("source_type") or ""
        source_id = item.get("source_id") or ""
        lines.append(f"{i}. **{source_type}** | `{source_id}`")
        lines.append(f"   - title: {item.get('title') or ''}")
        lines.append(f"   - url: {item.get('source_url') or ''}")
        lines.append(f"   - skipped_at: {item.get('skipped_at') or ''}")
    return "\n".join(lines)


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--sources", default="github,backlog")
    parser.add_argument("--add", action="append", default=[], metavar="IDENTITY")
    parser.add_argument("--remove", action="append", default=[], metavar="IDENTITY")
    parser.add_argument("--list", action="store_true", dest="list_items")
    args = parser.parse_args()

    vault = args.vault or Path(__file__).resolve().parents[2]
    sources = [item.strip() for item in args.sources.split(",") if item.strip()]
    unknown = [item for item in sources if item not in SOURCE_FILES]
    if unknown:
        raise SystemExit(f"unsupported source: {', '.join(unknown)}")

    if not args.list_items and not args.add and not args.remove:
        raise SystemExit("specify --add, --remove, or --list")

    try:
        if args.add:
            identities = [parse_identity(text) for text in args.add]
            add_skipped(vault, identities, sources)
        if args.remove:
            identities = [parse_identity(text) for text in args.remove]
            remove_skipped(vault, identities)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    configure_stdout_utf8()
    if args.list_items:
        text = format_list_markdown(vault)
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
