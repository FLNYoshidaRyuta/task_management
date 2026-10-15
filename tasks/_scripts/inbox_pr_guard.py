"""開いている Inbox の下書き PR を種別ごとに1本へ揃える。

新規と更新は別ラベルで探す。同じ fingerprint の open PR があるときは何もしない。
違うときだけ、そのブランチを更新する。open が無いときだけ新しい PR を作る。

このスクリプトは PR を作らない。判定と、PR 本文へそのまま貼るマーカーを返す。
取得用トークンは使わない。リポジトリの gh 認証で open PR を読む。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import compare_inbox

LABELS = {
    "new": "inbox-new",
    "update": "inbox-update",
}
LIST_LIMIT = 50
MARKER_RE = re.compile(
    r"<!--\s*inbox-pr-guard:(new|update)\s*\n(.*?)-->",
    re.DOTALL,
)

GhRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


class GuardError(Exception):
    """増殖防止を確定できないときに上げる。"""


def candidate_identity(item: dict) -> str:
    source_type = str(item.get("source_type") or "").strip()
    source_id = str(item.get("source_id") or "").strip()
    updated = str(item.get("source_updated_at") or "").strip()
    return f"{source_type}:{source_id}@{updated}"


def render_marker(kind: str, identities: list[str]) -> str:
    if kind not in LABELS:
        raise GuardError(f"unknown kind: {kind}")
    body = "\n".join(identities)
    if body:
        body += "\n"
    return f"<!-- inbox-pr-guard:{kind}\n{body}-->"


def marker_identities(body: str, kind: str) -> list[str] | None:
    """マーカーが無いときは None。複数あり中身が違うときは GuardError。"""
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    found: list[list[str]] = []
    for found_kind, inner in MARKER_RE.findall(text):
        if found_kind != kind:
            continue
        lines = [line.strip() for line in inner.splitlines() if line.strip()]
        found.append(sorted(lines))
    if not found:
        return None
    first = found[0]
    if any(item != first for item in found[1:]):
        raise GuardError(f"{LABELS[kind]} の PR 本文に内容の違うマーカーが複数あります")
    return first


def public_candidate(item: dict) -> dict:
    return {key: value for key, value in item.items() if not str(key).startswith("_")}


def pr_ref(pr: dict) -> dict:
    number = pr.get("number")
    branch = pr.get("headRefName")
    if isinstance(number, str) and number.isdigit():
        number = int(number)
    branch_name = branch.strip() if isinstance(branch, str) else ""
    if not isinstance(number, int) or isinstance(number, bool) or not branch_name:
        raise GuardError("open PR の number または headRefName がありません")
    url = pr.get("url")
    title = pr.get("title")
    return {
        "number": number,
        "url": url if isinstance(url, str) else "",
        "headRefName": branch_name,
        "title": title if isinstance(title, str) else "",
    }


def decide(kind: str, candidates: list[dict], prs: list[dict]) -> dict:
    if kind not in LABELS:
        raise GuardError(f"unknown kind: {kind}")
    label = LABELS[kind]
    if len(prs) > 1:
        numbers = ", ".join(str(pr.get("number")) for pr in prs)
        raise GuardError(f"{label} の open PR が複数あります: {numbers}")

    identities = sorted(candidate_identity(item) for item in candidates)
    marker = render_marker(kind, identities)
    current = pr_ref(prs[0]) if prs else None
    base = {
        "label": label,
        "pr": current,
        "identities": identities,
        "body_marker": marker,
        "candidates": [public_candidate(item) for item in candidates],
    }
    if not identities:
        return {"action": "skip", "reason": "no_candidates", **base}
    if current is None:
        return {"action": "create", "reason": "no_open_pr", **base}

    recorded = marker_identities(str(prs[0].get("body") or ""), kind)
    if recorded is None:
        return {"action": "update", "reason": "marker_missing", **base}
    if recorded == identities:
        return {"action": "skip", "reason": "unchanged", **base}
    return {"action": "update", "reason": "fingerprint_changed", **base}


def build_plan(compare_result: dict, open_prs: dict[str, list[dict]]) -> dict:
    buckets = compare_inbox.split_inbox(compare_result)
    return {
        "new": decide("new", buckets["new"], open_prs.get("new") or []),
        "update": decide("update", buckets["updated"], open_prs.get("update") or []),
        "attach": [public_candidate(item) for item in buckets["attach"]],
        "missing_from_cache": buckets["missing_from_cache"],
    }


def is_missing_label(message: str) -> bool:
    text = message.lower()
    if "label" not in text:
        return False
    return any(
        phrase in text
        for phrase in (
            "not found",
            "could not find",
            "no labels matched",
            "unknown label",
        )
    )


def default_runner(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def detect_repo(cwd: Path, runner: GhRunner) -> str:
    completed = runner(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        raise GuardError("リポジトリ名を取得できません" + (f"\n{message}" if message else ""))
    name = (completed.stdout or "").strip()
    if "/" not in name:
        raise GuardError(f"リポジトリ名を取得できません: {name}")
    return name


def list_open_prs(repo: str, label: str, cwd: Path, runner: GhRunner) -> list[dict]:
    completed = runner(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--label",
            label,
            "--limit",
            str(LIST_LIMIT),
            "--json",
            "number,url,title,body,headRefName",
        ],
        cwd,
    )
    message = (completed.stderr or completed.stdout or "").strip()
    if completed.returncode != 0:
        if is_missing_label(message):
            return []
        raise GuardError(f"open PR の取得に失敗しました: {label}" + (f"\n{message}" if message else ""))
    raw = (completed.stdout or "").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GuardError(f"open PR の JSON を読めません: {label}") from exc
    if not isinstance(payload, list):
        raise GuardError(f"open PR の応答が配列ではありません: {label}")
    if len(payload) >= LIST_LIMIT:
        raise GuardError(
            f"{label} の open PR が {LIST_LIMIT} 件に達したため、増殖防止を確定できません"
        )
    prs: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            raise GuardError(f"open PR の要素がオブジェクトではありません: {label}")
        prs.append(item)
    return prs


def load_compare(vault: Path, sources: list[str], compare_json: Path | None) -> dict:
    if compare_json is not None:
        try:
            data = json.loads(compare_json.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GuardError(f"compare JSON を読めません: {compare_json}") from exc
        if not isinstance(data, dict):
            raise GuardError("compare JSON がオブジェクトではありません")
        return data
    try:
        return compare_inbox.compare(vault, sources)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise GuardError(str(exc)) from exc


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def plan_with_gh(
    vault: Path,
    sources: list[str],
    compare_json: Path | None,
    runner: GhRunner,
) -> dict:
    compare_result = load_compare(vault, sources, compare_json)
    repo = detect_repo(vault, runner)
    open_prs = {
        kind: list_open_prs(repo, label, vault, runner) for kind, label in LABELS.items()
    }
    return build_plan(compare_result, open_prs)


def main(argv: list[str] | None = None, runner: GhRunner | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--sources", default="github,backlog")
    parser.add_argument("--compare-json", type=Path)
    args = parser.parse_args(argv)

    vault = (args.vault or Path(__file__).resolve().parents[2]).resolve()
    sources = [item.strip() for item in args.sources.split(",") if item.strip()]
    unknown = [item for item in sources if item not in compare_inbox.SOURCE_FILES]
    if unknown:
        raise SystemExit(f"unsupported source: {', '.join(unknown)}")
    if not sources and args.compare_json is None:
        raise SystemExit("sources is empty")

    try:
        plan = plan_with_gh(vault, sources, args.compare_json, runner or default_runner)
    except GuardError as exc:
        raise SystemExit(str(exc)) from exc

    configure_stdout_utf8()
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
