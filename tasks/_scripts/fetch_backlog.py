"""担当の Backlog 課題を sources/backlog/ へ取得する。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

from runtime_env import load_env_file

PROJECTS_FILE = Path("tasks/_config/backlog-projects.json")
STATUSES_FILE = Path("tasks/_config/backlog-statuses.json")
OUTPUT_FILE = Path("sources/backlog/assigned-issues.json")
PAGE_COUNT = 100
CLOSED_STATUS_NAMES = frozenset({"完了", "却下"})

JsonGetter = Callable[[str, dict | None], object]


def require_backlog_credentials(vault: Path) -> tuple[str, str]:
    load_env_file(vault / ".env")
    base_url = os.environ.get("BACKLOG_BASE_URL", "").strip()
    api_key = os.environ.get("BACKLOG_API_KEY", "").strip()
    if not base_url or not api_key:
        raise RuntimeError("BACKLOG_BASE_URL and BACKLOG_API_KEY are required")
    return base_url, api_key


def build_url(base_url: str, api_key: str, path: str, query: dict | None = None) -> str:
    params: list[tuple[str, str]] = []
    for key, value in (query or {}).items():
        if isinstance(value, list):
            for item in value:
                params.append((key, str(item)))
        else:
            params.append((key, str(value)))
    params.append(("apiKey", api_key))
    return f"{base_url.rstrip('/')}{path}?{urllib.parse.urlencode(params)}"


def http_get_json(base_url: str, api_key: str, path: str, query: dict | None = None) -> object:
    url = build_url(base_url, api_key, path, query)
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"backlog api failed: {path} ({exc.code}) {body}") from exc
    text = payload.strip()
    if not text:
        return None
    return json.loads(text)


def as_list(payload: object) -> list:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise RuntimeError("unexpected backlog api response")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def read_json_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"config is not an object: {path}")
    return data


def read_optional_config(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return read_json_config(path)


def default_status_include(status_name: str) -> bool:
    return status_name not in CLOSED_STATUS_NAMES


def fetch_filter_ids(projects_config: dict, statuses_config: dict) -> tuple[list[int], list[int]]:
    project_ids: list[int] = []
    for row in projects_config.get("projects") or []:
        if not isinstance(row, dict) or row.get("include") is not True:
            continue
        project_ids.append(int(row["projectId"]))
    if not project_ids:
        return [], []

    included = set(project_ids)
    status_ids: list[int] = []
    seen: set[int] = set()
    for row in statuses_config.get("statuses") or []:
        if not isinstance(row, dict) or row.get("include") is not True:
            continue
        project_id = int(row["projectId"])
        if project_id not in included:
            continue
        status_id = int(row["statusId"])
        if status_id in seen:
            continue
        seen.add(status_id)
        status_ids.append(status_id)
    return project_ids, status_ids


def nested(source: object, fields: dict[str, str]) -> dict | None:
    if not isinstance(source, dict):
        return None
    return {out_key: source.get(in_key) for out_key, in_key in fields.items()}


def normalize_issue(issue: dict, base_url: str) -> dict:
    issue_key = issue.get("issueKey")
    if not isinstance(issue_key, str) or not issue_key:
        raise RuntimeError("backlog issue is missing issueKey")
    return {
        "sourceType": "backlog_issue",
        "sourceId": issue_key,
        "sourceUrl": f"{base_url.rstrip('/')}/view/{issue_key}",
        "sourceUpdatedAt": issue.get("updated"),
        "id": issue.get("id"),
        "issueKey": issue_key,
        "summary": issue.get("summary"),
        "description": issue.get("description"),
        "project": nested(issue.get("project"), {"id": "id", "key": "projectKey", "name": "name"}),
        "status": nested(issue.get("status"), {"id": "id", "name": "name"}),
        "priority": nested(issue.get("priority"), {"id": "id", "name": "name"}),
        "assignee": nested(issue.get("assignee"), {"id": "id", "name": "name"}),
        "startDate": issue.get("startDate"),
        "dueDate": issue.get("dueDate"),
        "estimatedHours": issue.get("estimatedHours"),
        "created": issue.get("created"),
        "updated": issue.get("updated"),
    }


def refresh_statuses(vault: Path, get_json: JsonGetter) -> None:
    print("Refreshing Backlog project and status config...")
    existing_projects = read_optional_config(vault / PROJECTS_FILE)
    existing_statuses = read_optional_config(vault / STATUSES_FILE)

    project_include: dict[int, bool] = {}
    if existing_projects:
        for row in existing_projects.get("projects") or []:
            if isinstance(row, dict) and "projectId" in row:
                project_include[int(row["projectId"])] = bool(row.get("include"))

    status_include: dict[tuple[int, int], bool] = {}
    if existing_statuses:
        for row in existing_statuses.get("statuses") or []:
            if isinstance(row, dict) and "projectId" in row and "statusId" in row:
                key = (int(row["projectId"]), int(row["statusId"]))
                status_include[key] = bool(row.get("include"))

    merged_projects = []
    for project in as_list(get_json("/api/v2/projects", None)):
        project_id = int(project["id"])
        merged_projects.append(
            {
                "projectId": project_id,
                "projectKey": project.get("projectKey"),
                "projectName": project.get("name"),
                "include": project_include.get(project_id, True),
            }
        )
    merged_projects.sort(key=lambda row: str(row.get("projectKey") or ""))

    merged_statuses = []
    for project in merged_projects:
        if not project["include"]:
            continue
        api_statuses = as_list(
            get_json(f"/api/v2/projects/{project['projectId']}/statuses", None)
        )
        for status in api_statuses:
            status_id = int(status["id"])
            status_name = status.get("name") if isinstance(status.get("name"), str) else ""
            key = (project["projectId"], status_id)
            merged_statuses.append(
                {
                    "projectId": project["projectId"],
                    "projectKey": project["projectKey"],
                    "projectName": project["projectName"],
                    "statusId": status_id,
                    "statusName": status_name,
                    "include": status_include.get(key, default_status_include(status_name)),
                }
            )

    write_json(vault / PROJECTS_FILE, {"projects": merged_projects})
    write_json(vault / STATUSES_FILE, {"statuses": merged_statuses})
    print("")
    print("Backlog config updated.")
    print(f"Projects: {len(merged_projects)}")
    print(f"Statuses: {len(merged_statuses)}")
    print(f"Output: {PROJECTS_FILE.as_posix()}")
    print(f"Output: {STATUSES_FILE.as_posix()}")


def skip_fetch(message: str) -> None:
    print("")
    print(f"Backlog fetch skipped: {message}")
    print("Existing cache was not modified.")


def fetch_assigned(vault: Path, get_json: JsonGetter, base_url: str) -> None:
    print("Fetching Backlog user...")
    me = get_json("/api/v2/users/myself", None)
    if not isinstance(me, dict) or me.get("id") is None:
        raise RuntimeError("unexpected backlog user response")
    print(f"User: {me.get('name')} (ID: {me.get('id')})")

    try:
        projects_config = read_json_config(vault / PROJECTS_FILE)
        statuses_config = read_json_config(vault / STATUSES_FILE)
        project_ids, status_ids = fetch_filter_ids(projects_config, statuses_config)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        skip_fetch(str(exc))
        return

    if not project_ids or not status_ids:
        skip_fetch("no included projectId or statusId in config.")
        return

    print("Fetching assigned issues...")
    print(f"Included projects: {len(project_ids)}")
    print(f"Included statuses: {len(status_ids)}")

    all_issues: list[dict] = []
    offset = 0
    while True:
        page = as_list(
            get_json(
                "/api/v2/issues",
                {
                    "assigneeId[]": [me["id"]],
                    "projectId[]": project_ids,
                    "statusId[]": status_ids,
                    "sort": "updated",
                    "order": "desc",
                    "count": PAGE_COUNT,
                    "offset": offset,
                },
            )
        )
        all_issues.extend(page)
        if len(page) < PAGE_COUNT:
            break
        offset += PAGE_COUNT

    print(f"Found: {len(all_issues)} issues")
    result = [normalize_issue(issue, base_url) for issue in all_issues]
    write_json(vault / OUTPUT_FILE, result)
    print("")
    print("Backlog data updated.")
    print(f"Issues: {len(result)}")
    print(f"Output: {OUTPUT_FILE.as_posix()}")


def configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--refresh-statuses", action="store_true")
    args = parser.parse_args()
    vault = args.vault or Path(__file__).resolve().parents[2]
    try:
        base_url, api_key = require_backlog_credentials(vault)
        getter: JsonGetter = lambda path, query: http_get_json(base_url, api_key, path, query)
        if args.refresh_statuses:
            refresh_statuses(vault, getter)
        else:
            fetch_assigned(vault, getter, base_url)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    configure_stdout_utf8()


if __name__ == "__main__":
    main()
