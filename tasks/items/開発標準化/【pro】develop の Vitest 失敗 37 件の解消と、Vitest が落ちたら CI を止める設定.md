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
github_repo: ''
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4325
backlog_url: '[REDACTED]/view/MYPL-4325'
backlog_updated_at: 2026-11-11T11:28:42Z
---
## 概要

MYPL-4193 から画面側テストの分だけを切り出した課題（設計ドメイン「リポジトリごとのコーディングルール」のテスト管理）。PHPUnit は #1442 で直し、#1486 で失敗したら CI が止まる設定にした。一方 Vitest は CI のジョブが non-blocking のままで、失敗しても CI が緑に見える。2026-11-11 の develop の CI（run 42945703809）では Vitest が 37 件失敗（shard 1/2: 23 件・9 ファイル、shard 2/2: 14 件・8 ファイル）。起票時（9/29）の 20 件から増加。例として window is not defined、ファイル行数の上限チェック（ADR-0023）、ベトナム語ラベル「Ngày」の要素が見つからない、など。やることは、(1) 既存の失敗を直すか古いテストを整理する、(2) Vitest のジョブを blocking にして新しく壊れたら気づけるようにする。参照: https://github.com/FutureLinkNetwork/mypl_pro/actions/runs/42945703809

## やったこと

## 残りのやること
