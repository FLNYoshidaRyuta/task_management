"""status / priority / source_type の単一選択リストを読む。"""

from __future__ import annotations


def single_choice(value) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0].strip()
    return ""


STATUS_CHOICES = (
    "todo",
    "in_progress",
    "to_release",
    "done",
    "canceled",
)
PRIORITY_CHOICES = (
    "Critical_bug",
    "bug",
    "High",
    "Mid",
    "Low",
)
SOURCE_TYPE_CHOICES = (
    "routine",
)

GITHUB_TYPE_CHOICES = (
    "github_issue",
    "github_pr",
)

PROPERTY_CHOICES = {
    "status": STATUS_CHOICES,
    "priority": PRIORITY_CHOICES,
    "source_type": SOURCE_TYPE_CHOICES,
    "github_type": GITHUB_TYPE_CHOICES,
}

SINGLE_CHOICE_FIELDS = {
    key: frozenset(choices) for key, choices in PROPERTY_CHOICES.items()
}
