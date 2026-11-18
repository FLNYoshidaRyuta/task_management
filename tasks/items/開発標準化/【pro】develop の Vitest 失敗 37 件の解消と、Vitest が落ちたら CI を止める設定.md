---
task_id: 115
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
backlog_url: https://fln2000.backlog.com/view/MYPL-4325  # pragma: allowlist secret
backlog_updated_at: 2026-11-11 11:28:42+00:00
---

## 概要

MYPL-4193 から画面側テスト分を切り出した課題。PHPUnit は修正済みで、失敗時に CI を止める設定も済んでいる。Vitest は non-blocking のまま。

2026-11-11 の develop CI（GitHub Actions run 42945703809、https://github.com/FutureLinkNetwork/mypl_pro/actions/runs/42945703809）で Vitest が 37 件失敗（shard1: 23 件・9 ファイル、shard2: 14 件・8 ファイル）。起票時の 20 件から増加している。

やることは失敗の解消または古いテストの整理と、Vitest ジョブを blocking 化すること。

## やったこと

## 残りのやること