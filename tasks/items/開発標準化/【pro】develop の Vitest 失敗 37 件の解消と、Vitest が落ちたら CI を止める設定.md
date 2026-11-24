---
task_id: 116
title: 【pro】develop の Vitest 失敗 37 件の解消と、Vitest が落ちたら CI を止める設定
project: 開発標準化
status:
- todo
start: ''
end: ''
focus_date:
priority: []
estimate:
depends_on: []
related: []
github_type: []
github_repo: ''
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4325
backlog_url: "[REDACTED]/view/MYPL-4325"
backlog_updated_at: 2026-11-11 11:28:42+00:00
---
## 概要

MYPL-4193 から画面側テスト分を切り出し。

Vitest CI non-blocking。11/11 develop CI で37件失敗（shard1 23件/9ファイル、shard2 14件/8ファイル）。

やること: 失敗修正または古いテスト整理、Vitest blocking化。

PHPUnit は既に対応済みの記載あり。

## やったこと

## 残りのやること