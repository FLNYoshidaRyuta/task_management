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
backlog_url: https://fln2000.backlog.com/view/MYPL-4325  # pragma: allowlist secret
backlog_updated_at: 2026-11-11T11:28:42Z
---
## 概要

MYPL-4193から画面側テスト分を切り出し。PHPUnitは#1442と#1486でCI停止設定済み。Vitestはnon-blockingのまま。11/11 develop CI run 42945703809でVitest37件失敗（shard1/2: 23件9ファイル、shard2/2: 14件8ファイル）。起票時20件から増加。例: window is not defined、ADR-0023行数上限、ベトナム語ラベルNgày要素なし等。やること: 既存失敗の修正または古いテスト整理、Vitestジョブをblocking化。

## やったこと

## 残りのやること