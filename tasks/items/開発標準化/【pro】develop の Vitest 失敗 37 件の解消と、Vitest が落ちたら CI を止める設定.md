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
backlog_url: https://fln2000.backlog.com/view/MYPL-4325  # pragma: allowlist secret
backlog_updated_at: 2026-11-11T11:28:42Z
---
## 概要

- MYPL-4193 から画面側テストの分だけを切り出した課題（設計ドメイン「リポジトリごとのコーディングルール」のテスト管理）
- PHPUnit は #1442 で直し、#1486 で失敗したら CI が止まる設定にした。Vitest は CI のジョブが non-blocking のままで失敗しても CI が緑に見える
- 11/11 develop CI run 42945703809 で Vitest 37 件失敗（shard1 23件9ファイル、shard2 14件8ファイル）。起票時9/29の20件から増加。例: window is not defined、ファイル行数上限チェック ADR-0023、ベトナム語ラベル Ngày の要素が見つからない など
- やること: 既存失敗を直すか古いテストを整理する / Vitest ジョブを blocking にする
- GitHub Actions: https://github.com/FutureLinkNetwork/mypl_pro/actions/runs/42945703809

## やったこと

## 残りのやること

