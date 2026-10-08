# ADR 0004: 1タスクに GitHub と Backlog のポインタを持たせる

- Status: Accepted
- Date: 2026-10-09

## Context

同じ作業を GitHub Issue と Backlog 課題で別ファイルにすると、一覧の件数と `related` が増え、作業量より多く見える。Inbox 照合も `source_type` と `source_id` の1組前提で、二重管理の片方が常に新規候補に出ていた。

## Decision

- 非ルーティーンの個人タスクは、GitHub を0または1件、Backlog を0または1件までポインタとして持つ。
- GitHub は `github_type`（`github_issue` または `github_pr`）、`github_id`、`github_url`、`github_updated_at` で表す。
- Backlog は `backlog_id`、`backlog_url`、`backlog_updated_at` で表す。
- ルーティーン生成タスクだけ `source_type: routine` と `source_id` を使う。
- Inbox 照合は各チャンネルの id で紐づける。キャッシュ欠落はチャンネル単位で報告する。
- キャッシュ本文の GitHub URL や `MYPL-` 参照から、既存タスク1件にだけ当たる場合は `attach_to` として追記候補に出す。ファイルへの書き込みはユーザー指示後の task-manager のみ。
- 同一作業の統合判断は人間が行う。削除した `task_id` は再利用しない。

## Consequences

- 旧 `source_type` / `source_id` / `source_url` / `source_updated_at` は非ルーティーンでは使わない。
- `compare_inbox.py` と `validate_task_properties.py` が新形式を正本とする。
- 二重管理を解消したタスクは1ファイルに両チャンネルのポインタを載せる。
