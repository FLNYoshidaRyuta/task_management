---
task_id: 114
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
github_repo:
github_id:
github_url:
github_updated_at:
backlog_id: MYPL-4325
backlog_url: https://fln2000.backlog.com/view/MYPL-4325  # pragma: allowlist secret
backlog_updated_at: 2026-11-11 11:28:42+00:00
---
## 概要

MYPL-4193 から分割（画面側テストのみ）。設計ドメイン「repo coding rules」のテスト管理。

PHPUnit は #1442 で修正済み。PHPUnit 失敗時に CI を止める設定は #1486。

Vitest の CI ジョブは non-blocking で、Vitest が失敗しても CI は緑のまま。

develop の CI run 42945703809（2026-11-11）: Vitest 37 failures（shard1: 9 files で 23、shard2: 8 files で 14）。チケット起票（9/29）時は 20 件だった。例: window is not defined、file line limit ADR-0023、Vietnamese label「Ngày」not found。

(1) 既存失敗の修正または古いテストの整理、(2) Vitest ジョブを blocking にする。

https://github.com/FutureLinkNetwork/mypl_pro/actions/runs/42945703809

## やったこと

## 残りのやること

