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
    dependency = [
        "# 依存関係図",
        "",
        "```mermaid",
        "flowchart LR",
    ]

    path_to_id = {}
    title_to_ids = {}

    for index, task in enumerate(tasks):
        node_id = f"T{index}"
        title = as_text(task.get("title"))
        path = task_link_path(task, vault_root)

        path_to_id[path] = node_id
        title_to_ids.setdefault(title, []).append(node_id)
        dependency.append(
            f'    {node_id}["{mermaid_text(title)}"]'
        )

    for task in tasks:
        target_id = path_to_id.get(task_link_path(task, vault_root))

        for dep in task.get("depends_on", []) or []:
            dep_id = resolve_dependency_id(dep, path_to_id, title_to_ids)

            if dep_id and target_id and dep_id != target_id:
                dependency.append(
                    f"    {dep_id} --> {target_id}"
                )

    dependency += [
        "```",
        "",
    ]

    return "\n".join(dependency)


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

            title = mermaid_text(task.get("title"))
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

    print(f"Generated views from {len(tasks)} task(s).")


if __name__ == "__main__":
    main()