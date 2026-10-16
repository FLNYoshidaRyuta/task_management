---
task_id: 41
title: '[テスト基盤] MyplkunAgentServiceTest のヘルパーが migration に存在しない AGENT_DRAFT_ID カラムを作りスキーマ
  drift でバグを隠す'
project: 開発標準化
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#665
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/665
github_updated_at: 2026-09-16 15:24:25+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

`tests/Unit/Services/MyplkunAgentServiceTest.php` の `createRevisionContextTables()` が、実 migration に存在しない `AGENT_DRAFT_ID` カラムを AGENT_DRAFT_GENERATIONS 相当のテーブルへ作成している。

## やったこと

- テストヘルパーのテーブル定義を実 migration と突き合わせ、存在しないカラムを除去する（または実 migration から生成する）
- 同型の drift が他のヘルパー定義テーブルにないか棚卸しする
- #660（発見元。修正はテストローカルの DROP で回避済み）
- 証跡: orchestrator reports/lane339/worker-a-php-report.md

## 残りのやること

- テストヘルパーのテーブル定義を実 migration と突き合わせ、存在しないカラムを除去する（または実 migration から生成する）
- 同型の drift が他のヘルパー定義テーブルにないか棚卸しする
- #660（発見元。修正はテストローカルの DROP で回避済み）
- 証跡: orchestrator reports/lane339/worker-a-php-report.md
