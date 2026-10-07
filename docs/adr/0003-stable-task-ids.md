# ADR 0003: 個人タスクに安定した通し番号 id を付ける

- Status: Accepted
- Date: 2026-10-07

## Context

タスクの title は長く、Cursor への指示で毎回書くのが不便である。
ファイルパスもプロジェクト名を含み、口頭・チャットでの指定に向かない。

ルーティーン定義の `id`、外部 Issue 番号、`source_id` は個人タスクの指示用 ID として使えない。

## Decision

個人タスクの指示用 ID は、各タスクファイル frontmatter の正の整数 `task_id` とする。
Obsidian の予約プロパティ `id` とは別である。

採番と欠番の維持は `tasks/_scripts/assign_task_ids.py` が行う。
エージェントは `task_id` を自分で書かず、既存の `task_id` を変更しない。

次に割り当てる番号のカーソルだけ `tasks/_config/task-id.json` の `next_id` に保持する。
タスクを削除しても番号は再利用しない。

初回採番の順序は `tasks/_タスク.md` のタスクツリーに出てくる順。
ツリーに無いファイルはその後、パス順。

タスクツリーのリンク表示名は `{id} {title}` に揃える。
ガントチャート、依存関係図、関連図のノード表示名も同じ形式にする。

## Consequences

「タスク 12」は `task_id: 12` の個人タスクを指す。
一覧（Bases）では列名 `id` で `task_id` を表示する。
task-manager の操作後は `generate_routines.py` の次に `assign_task_ids.py` を実行する。

ルーティーン定義の `id` や Backlog / GitHub の番号とは別物として扱う。
