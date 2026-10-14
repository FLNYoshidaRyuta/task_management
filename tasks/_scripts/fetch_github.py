"""担当 Issue、自分の PR、レビュー依頼を sources/github/ へ取得する。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from normalize_github import normalize
from runtime_env import gh_env, load_env_file

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
            "Failed to fetch GitHub user. Set GH_TOKEN to the account whose issues should be fetched."
            + (f"\n{message}" if message else "")
        )
    login = completed.stdout.strip()
    if not login:
        raise RuntimeError(
            "Failed to fetch GitHub user. Set GH_TOKEN to the account whose issues should be fetched."
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


def fetch(vault: Path, runner: GhRunner | None = None) -> None:
    load_env_file(vault / ".env")
    login = read_github_login(runner)
    print(f"GitHub user: {login}")

    for source_type, relative, args, label in SEARCHES:
        print(label)
        items = gh_json(args, runner)
        write_json(vault / relative, normalize(items, source_type))

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
