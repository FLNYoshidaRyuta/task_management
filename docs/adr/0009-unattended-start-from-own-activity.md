# ADR 0009: 無人 Inbox は自分の活動で todo を in_progress にできる

- Status: Accepted
- Date: 2026-10-28

## Context

無人 Inbox は下書き PR でタスクの新規作成と本文更新を行う。着手（`in_progress`）は原則として人間の判断だが、自分のオープンな GitHub PR と自分の会話コメントは機械的に判定できる。

Backlog では PR 連携を信号にしない。課題への自分のコメント追加だけを対象にする。

## Decision

無人 Inbox（`.cursor/skills/task-inbox-unattended/SKILL.md`）だけ、次の条件で `status: todo` を `in_progress` に変えてよい。

1. **GitHub Issue**: 開いている自分の PR の `closingIssues` にその Issue が含まれる（下書き PR を含む）。
2. **GitHub Issue または Backlog 課題**: 会話コメントの作者が自分で、`createdAt` がタスクの当該チャンネルの `*_updated_at` より新しい。

`to_release`、`done`、`canceled` は変えない。条件が消えても `in_progress` から戻さない。

判定は `tasks/_scripts/inbox_progress.py` が行い、`inbox_pr_guard.py` の JSON に `status`（新規）と `status_changes`（更新）を載せる。対話 Inbox は変えない。

## Consequences

- `fetch_github.py` は `my-prs.json` に `closingIssues` を付与し、`viewer.json` に login を書く。
- `fetch_backlog.py` は `viewer.json` にユーザー id を書く。PR 一覧は取らない。
- `fetch_comments.py` は Backlog コメントに `authorId` を付与し、`--inbox-updates` で `cache_newer` 候補のコメントを取る。
- 無人エージェントは guard の JSON だけを `task-manager` に渡し、status を推測しない。
