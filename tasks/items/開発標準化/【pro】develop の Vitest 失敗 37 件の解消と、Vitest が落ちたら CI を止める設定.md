---
task_id: 116
title: 【pro】develop の Vitest 失敗 37 件の解消と、Vitest が落ちたら CI を止める設定
project: 開発標準化
status:
  - todo
start: ''
end: ''
focus_date: ''
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
backlog_updated_at: '2026-11-11T11:28:42Z'
---
## 概要

MYPL-4193 から画面側テストの分だけを切り出した課題（設計ドメイン「リポジトリごとのコーディングルール」のテスト管理）。PHPUnit は #1442 で直し、#1486 で失敗したら CI が止まる設定。Vitest は CI のジョブが non-blocking のまま。11/11 develop CI（run 42945703809）で Vitest 37 件失敗（shard1 23件/9ファイル、shard2 14件/8ファイル）。起票時 20 件から増加。やることは既存失敗の解消または古いテスト整理、Vitest ジョブを blocking にする。

## やったこと

## 残りのやること