"""担当 Issue、自分の PR、レビュー依頼を sources/github/ へ取得する。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from normalize_github import normalize
from runtime_env import GITHUB_FETCH_TOKEN, gh_env, load_env_file

GITHUB_DIR = Path("sources/github")
SEARCHES = (
    (
        "github_issue",
        GITHUB_DIR / "assigned-issues.json",
        (
            "search",
            "issues",
            "--assignee=@me",
            "--state=open",
            "--limit=100",
            "--json",
            "number,title,body,state,repository,labels,assignees,author,createdAt,updatedAt,url",
        ),
        "Fetching assigned issues...",
    ),
    (
        "github_pr",
        GITHUB_DIR / "my-prs.json",
        (
            "search",
            "prs",
            "--author=@me",
            "--state=open",
            "--limit=100",
            "--json",
            "number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url",
        ),
        "Fetching my PRs...",
    ),
    (
        "github_pr",
        GITHUB_DIR / "review-requests.json",
        (
            "search",
            "prs",
            "--review-requested=@me",
            "--state=open",
            "--limit=100",
            "--json",
            "number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url",
        ),
        "Fetching review requests...",
    ),
)

GhRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def run_gh(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=gh_env(),
    )


def read_github_login(runner: GhRunner | None = None) -> str:
    completed = (runner or run_gh)(("api", "user", "--jq", ".login"))
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"Failed to fetch GitHub user. Set {GITHUB_FETCH_TOKEN} to the account whose issues should be fetched."
            + (f"\n{message}" if message else "")
        )
    login = completed.stdout.strip()
    if not login:
        raise RuntimeError(
            f"Failed to fetch GitHub user. Set {GITHUB_FETCH_TOKEN} to the account whose issues should be fetched."
        )
    return login


def gh_json(args: Sequence[str], runner: GhRunner | None = None) -> list:
    completed = (runner or run_gh)(args)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Failed to fetch GitHub data: gh {' '.join(args)}\n{message}")
    raw = completed.stdout.strip()
    items = json.loads(raw) if raw else []
    if isinstance(items, dict):
        return [items]
    if not isinstance(items, list):
        raise RuntimeError("unexpected gh response")
    return items


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_owner_repo_number(source_id: str) -> tuple[str, str]:
    if "#" not in source_id:
        raise ValueError(f"invalid github sourceId: {source_id}")
    owner_repo, number = source_id.rsplit("#", 1)
    if not owner_repo or not number.strip():
        raise ValueError(f"invalid github sourceId: {source_id}")
    return owner_repo, number.strip()


def closing_issue_ids_from_pr_view(payload: dict) -> list[str]:
    refs = payload.get("closingIssuesReferences")
    if not isinstance(refs, list):
        return []
    result: list[str] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        number = ref.get("number")
        repository = ref.get("repository")
        if number is None or not isinstance(repository, dict):
            continue
        owner = repository.get("owner")
        name = repository.get("name")
        if not isinstance(owner, dict) or not isinstance(name, str):
            continue
        login = owner.get("login")
        if not isinstance(login, str) or not login.strip() or not name.strip():
            continue
        result.append(f"{login.strip()}/{name.strip()}#{number}")
    return result


def enrich_my_prs(items: list[dict], runner: GhRunner) -> None:
    for item in items:
        source_id = item.get("sourceId")
        if not isinstance(source_id, str):
            raise RuntimeError("GitHub PR item is missing sourceId")
        owner_repo, number = parse_owner_repo_number(source_id)
        completed = runner(
            (
                "pr",
                "view",
                number,
                "--repo",
                owner_repo,
                "--json",
                "closingIssuesReferences,isDraft,state",
            )
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"Failed to fetch closing issues for PR {source_id}: {message}"
            )
        raw = completed.stdout.strip()
        payload = json.loads(raw) if raw else {}
        if not isinstance(payload, dict):
            raise RuntimeError(f"unexpected gh pr view response for {source_id}")
        item["closingIssues"] = closing_issue_ids_from_pr_view(payload)
        if payload.get("isDraft") is not None:
            item["isDraft"] = payload.get("isDraft")
        if isinstance(payload.get("state"), str):
            item["state"] = payload.get("state")


def fetch(vault: Path, runner: GhRunner | None = None) -> None:
    gh = runner or run_gh
    load_env_file(vault / ".env")
    login = read_github_login(gh)
    print(f"GitHub user: {login}")
    write_json(vault / GITHUB_DIR / "viewer.json", {"login": login})

    my_prs_path = GITHUB_DIR / "my-prs.json"

    for source_type, relative, args, label in SEARCHES:
        print(label)
        items = gh_json(args, gh)
        normalized = normalize(items, source_type)
        if relative == my_prs_path:
            enrich_my_prs(normalized, gh)
        write_json(vault / relative, normalized)

    print("")
    print("GitHub data updated.")


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    args = parser.parse_args()
    vault = args.vault or Path(__file__).resolve().parents[2]
    try:
        fetch(vault)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    configure_stdout_utf8()


if __name__ == "__main__":
    main()
