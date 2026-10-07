from pathlib import Path
import re
import yaml

TASKS_DIR = Path(__file__).resolve().parent.parent
ITEMS_DIR = TASKS_DIR / "items"


def load_task(path: Path):
    text = path.read_text(encoding="utf-8")

    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return None

    data = yaml.safe_load(match.group(1)) or {}
    data["_path"] = path

    return data


def as_text(value):
    if value is None:
        return ""
    return str(value)


def mermaid_text(value):
    return (
        as_text(value)
        .replace(":", "：")
        .replace(",", "，")
        .replace("\n", " ")
    )


def task_display_label(task):
    title = as_text(task.get("title"))
    raw_id = task.get("task_id", task.get("id"))

    if isinstance(raw_id, bool):
        return title

    if isinstance(raw_id, int) and raw_id > 0:
        return f"{raw_id} {title}"

    if isinstance(raw_id, str) and raw_id.strip().isdigit():
        parsed = int(raw_id.strip())

        if parsed > 0:
            return f"{parsed} {title}"

    return title


def task_mermaid_label(task):
    return mermaid_text(task_display_label(task))


def task_link_path(task, vault_root: Path):
    rel = task["_path"].resolve().relative_to(vault_root.resolve()).as_posix()

    if rel.endswith(".md"):
        rel = rel[:-3]

    return rel


def parse_dependency_ref(value):
    value = str(value).strip()
    match = re.match(r"\[\[(.*?)(?:\|(.*?))?\]\]$", value)

    if not match:
        return None, value

    path = match.group(1).replace("\\", "/")

    if path.endswith(".md"):
        path = path[:-3]

    alias = match.group(2)

    if alias:
        return path, alias

    return path, Path(path).name


def resolve_dependency_id(value, path_to_id, title_to_ids):
    path, label = parse_dependency_ref(value)

    if path and path in path_to_id:
        return path_to_id[path]

    ids = title_to_ids.get(label, [])

    if len(ids) == 1:
        return ids[0]

    return None


def render_dependency(tasks, vault_root: Path):
    path_to_id = {}
    title_to_ids = {}
    path_to_title = {}

    for index, task in enumerate(tasks):
        node_id = f"T{index}"
        path = task_link_path(task, vault_root)
        title = task_display_label(task)

        path_to_id[path] = node_id
        path_to_title[path] = title
        title_to_ids.setdefault(title, []).append(node_id)

    edges = []

    for task in tasks:
        target_path = task_link_path(task, vault_root)

        for dep in task.get("depends_on", []) or []:
            dep_path = resolve_task_path(dep, path_to_id, title_to_ids)

            if dep_path and target_path and dep_path != target_path:
                edges.append((dep_path, target_path))

    participating = sorted({path for edge in edges for path in edge})

    if not participating:
        return "# 依存関係図\n\n依存関係はありません。\n"

    lines = [
        "# 依存関係図",
        "",
        "```mermaid",
        "flowchart LR",
    ]

    local_ids = {path: f"T{index}" for index, path in enumerate(participating)}

    for path in participating:
        local_id = local_ids[path]
        lines.append(f'    {local_id}["{mermaid_text(path_to_title[path])}"]')

    for dep_path, target_path in sorted(edges):
        lines.append(f"    {local_ids[dep_path]} --> {local_ids[target_path]}")

    lines.extend(
        [
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def resolve_task_path(value, path_to_id, title_to_ids):
    path, label = parse_dependency_ref(value)

    if path and path in path_to_id:
        return path

    ids = title_to_ids.get(label, [])

    if len(ids) == 1:
        node_id = ids[0]
        for candidate, candidate_id in path_to_id.items():
            if candidate_id == node_id:
                return candidate

    return None


def render_related(tasks, vault_root: Path):
    path_to_id = {}
    title_to_ids = {}
    path_to_title = {}

    for index, task in enumerate(tasks):
        node_id = f"T{index}"
        path = task_link_path(task, vault_root)
        title = task_display_label(task)

        path_to_id[path] = node_id
        path_to_title[path] = title
        title_to_ids.setdefault(title, []).append(node_id)

    directed = set()
    inconsistencies = []

    for task in tasks:
        source_path = task_link_path(task, vault_root)

        for ref in task.get("related", []) or []:
            target_path = resolve_task_path(ref, path_to_id, title_to_ids)

            if target_path is None:
                inconsistencies.append(
                    f"- 解決できないリンク: `{source_path}` の related に {ref!r} がある"
                )
                continue

            if target_path == source_path:
                inconsistencies.append(
                    f"- 自分自身: `{source_path}` の related に自分自身がある"
                )
                continue

            directed.add((source_path, target_path))

    edge_keys = set()
    for source_path, target_path in directed:
        edge_keys.add(tuple(sorted([source_path, target_path])))

    for source_path, target_path in directed:
        if (target_path, source_path) not in directed:
            inconsistencies.append(
                f"- 片側だけ: `{source_path}` の related に `{target_path}` がある"
            )

    lines = ["# 関連図", ""]

    if not edge_keys and not inconsistencies:
        lines.append("関連タスクはありません。")
        lines.append("")
        return "\n".join(lines)

    if edge_keys:
        participating = sorted({path for key in edge_keys for path in key})
        local_ids = {path: f"T{index}" for index, path in enumerate(participating)}

        lines.extend(
            [
                "```mermaid",
                "flowchart LR",
            ]
        )

        for path in participating:
            local_id = local_ids[path]
            lines.append(f'    {local_id}["{mermaid_text(path_to_title[path])}"]')

        for left, right in sorted(edge_keys):
            lines.append(f"    {local_ids[left]} --- {local_ids[right]}")

        lines.extend(
            [
                "```",
                "",
            ]
        )

    if inconsistencies:
        lines.append("## 不整合")
        lines.append("")
        lines.extend(inconsistencies)
        lines.append("")

    return "\n".join(lines)


def main():
    tasks = []

    for path in ITEMS_DIR.rglob("*.md"):
        task = load_task(path)

        if task:
            tasks.append(task)

    tasks.sort(
        key=lambda x: (
            as_text(x.get("project")),
            as_text(x.get("title")),
        )
    )

    # to_release は mermaid 標準の done / active に色がないため、id 接頭辞 rel で塗る。
    gantt_to_release_css = (
        "rect[id*=rel] { fill: #c2410c !important; stroke: #9a3412 !important; }"
    )

    gantt = [
        "# ガントチャート",
        "",
        "```mermaid",
        f"%%{{init: {{'themeCSS': '{gantt_to_release_css}'}}}}%%",
        "gantt",
        "    title ガントチャート",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %m/%d",
    ]

    projects = sorted(
        set(as_text(t.get("project")) for t in tasks)
    )

    counter = 0

    for project in projects:
        project_tasks = [
            t for t in tasks
            if as_text(t.get("project")) == project
        ]

        visible = [
            t for t in project_tasks
            if t.get("start") and t.get("end")
        ]

        if not visible:
            continue

        gantt.append(f"    section {mermaid_text(project)}")

        for task in visible:
            counter += 1

            title = task_mermaid_label(task)
            start = as_text(task.get("start"))
            end = as_text(task.get("end"))
            status = as_text(task.get("status"))

            prefix = ""
            task_id = f"t{counter}"

            if status == "done":
                prefix = "done, "
            elif status == "in_progress":
                prefix = "active, "
            elif status == "to_release":
                task_id = f"rel{counter}"

            # 同日は幅が 0 になるため、その日の 1 日タスクとして描く。
            span = "1d" if start == end else end
            gantt.append(
                f"    {title} :{prefix}{task_id}, {start}, {span}"
            )

    gantt += [
        "```",
        "",
    ]

    (TASKS_DIR / "ガントチャート.md").write_text(
        "\n".join(gantt),
        encoding="utf-8",
        newline="\n",
    )

    dependency = render_dependency(tasks, TASKS_DIR.parent)

    (TASKS_DIR / "依存関係図.md").write_text(
        dependency,
        encoding="utf-8",
        newline="\n",
    )

    related = render_related(tasks, TASKS_DIR.parent)

    (TASKS_DIR / "関連図.md").write_text(
        related,
        encoding="utf-8",
        newline="\n",
    )

    print(f"Generated views from {len(tasks)} task(s).")


if __name__ == "__main__":
    main()