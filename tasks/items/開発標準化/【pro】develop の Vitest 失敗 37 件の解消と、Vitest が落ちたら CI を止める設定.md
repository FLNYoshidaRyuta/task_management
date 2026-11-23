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
backlog_url: https://fln2000.backlog.com/view/MYPL-4325  # pragma: allowlist secret
backlog_updated_at: 2026-11-11T11:28:42Z
---
## 概要

MYPL-4193 から画面側テスト分を切り出した課題。PHPUnit は #1442 で修正、#1486 で CI blocking。Vitest は non-blocking のまま。

11/11 の develop CI（run 42945703809）で Vitest が 37 件失敗（shard 1/2: 23 件・9 ファイル、shard 2/2: 14 件・8 ファイル）。起票時（9/29）の 20 件から増加。例: `window is not defined`、ファイル行数上限（ADR-0023）、ベトナム語ラベル「Ngày」の要素が見つからない、など。

やることは既存の失敗を直すか古いテストを整理すること、および Vitest ジョブを blocking 化すること。

- https://github.com/FutureLinkNetwork/mypl_pro/actions/runs/42945703809

## やったこと

## 残りのやること

