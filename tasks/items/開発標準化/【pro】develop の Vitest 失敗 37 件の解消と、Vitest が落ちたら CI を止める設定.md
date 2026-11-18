---
task_id: 116
title: 【pro】develop の Vitest 失敗 37 件の解消と、Vitest が落ちたら CI を止める設定
priority: []
project: 開発標準化
status:
- todo
depends_on: []
github_type: []
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4325
backlog_url: "https://fln2000.backlog.com/view/MYPL-4325"  # pragma: allowlist secret
backlog_updated_at: '2026-11-11T11:28:42Z'
---
## 概要

MYPL-4193 から画面側テスト分を切り出した課題（設計ドメイン「リポジトリごとのコーディングルール」のテスト管理）。PHPUnit は #1442/#1486 で CI 停止設定済み。Vitest は non-blocking のまま。11/11 develop CI run 42945703809 で Vitest 37件失敗（shard1 23件/9ファイル、shard2 14件/8ファイル）。起票時20件から増加。やること: 失敗を直すか古いテスト整理、Vitest を blocking に。

## やったこと


## 残りのやること
