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


def dependency_title(value):
    value = str(value)

    # [[tasks/items/project/task|表示名]]
    match = re.match(r"\[\[(.*?)(?:\|(.*?))?\]\]", value)

    if match:
        path = match.group(1)
        alias = match.group(2)

        if alias:
            return alias

        return Path(path).name

    return value


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

# --------------------
# Gantt
# --------------------

# to_release は mermaid 標準の done / active に色がないため、id 接頭辞 rel で塗る。
GANTT_TO_RELEASE_CSS = (
    "rect[id*=rel] { fill: #c2410c !important; stroke: #9a3412 !important; }"
)

gantt = [
    "# ガントチャート",
    "",
    "```mermaid",
    f"%%{{init: {{'themeCSS': '{GANTT_TO_RELEASE_CSS}'}}}}%%",
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

        gantt.append(
            f"    {title} :{prefix}{task_id}, {start}, {end}"
        )

gantt += [
    "```",
    "",
]

(TASKS_DIR / "ガントチャート.md").write_text(
    "\n".join(gantt),
    encoding="utf-8",
)

# --------------------
# Dependency graph
# --------------------

dependency = [
    "# 依存関係図",
    "",
    "```mermaid",
    "flowchart LR",
]

title_to_id = {}

for index, task in enumerate(tasks):
    node_id = f"T{index}"
    title = as_text(task.get("title"))

    title_to_id[title] = node_id
    dependency.append(
        f'    {node_id}["{mermaid_text(title)}"]'
    )

for task in tasks:
    target_title = as_text(task.get("title"))
    target_id = title_to_id.get(target_title)

    for dep in task.get("depends_on", []) or []:
        dep_title = dependency_title(dep)
        dep_id = title_to_id.get(dep_title)

        if dep_id and target_id:
            dependency.append(
                f"    {dep_id} --> {target_id}"
            )

dependency += [
    "```",
    "",
]

(TASKS_DIR / "依存関係図.md").write_text(
    "\n".join(dependency),
    encoding="utf-8",
)

print(f"Generated views from {len(tasks)} task(s).")