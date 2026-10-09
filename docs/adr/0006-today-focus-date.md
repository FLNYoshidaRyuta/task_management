# ADR 0006: 今日やる判断を focus_date で持つ

- Status: Accepted
- Date: 2026-10-10

## Context

`tasks/タスクビュー.base` の「今日」ビューは、着手中（`in_progress`）または期限が当日（`end == today()`）のタスクを集める。人間が「今日やる」と決めた作業そのものを表す属性はなかった。

`TASK_MANAGEMENT_PRINCIPLES.md` では「今日やること」を派生ビューとして挙げているが、正本側のマークが無かった。

## Decision

- 今日やる判断は、各タスク frontmatter の任意属性 `focus_date`（`YYYY-MM-DD`）に持つ。
- 表示は `tasks/タスクビュー.base` の先頭ビュー「今日やる」。条件は未完了・未中止かつ `focus_date == today()`。
- `tasks/_タスク.md` に今日用の一覧見出しや埋め込みは足さない。
- 翌日に過去日付を自動削除するスクリプトは置かない。ビューの日付条件で自然に一覧から外れる。
- 既存の「今日」「現役」「1週間以内」ビューは残す。
- `focus_date` の形式は `tasks/_scripts/validate_task_properties.py` で検証する。キーが無いタスクは検査しない。

## Consequences

- Obsidian の「現役」一覧から「今日やる」列で日付を入れられる。`.obsidian/types.json` で `focus_date` は `date` 型。
- 着手中や期限当日でも `focus_date` が無ければ「今日やる」には出ない。逆に、期限外でも当日の `focus_date` で出る。
- エージェントはユーザー指示があるときだけ `focus_date` を更新する。
