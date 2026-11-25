---
task_id: 69
title: dev の Rundeck・cron に手動登録されたジョブを棚卸しし、yaml 管理に一本化する
project: 業務タスク
status:
  - done
start: ""
end: ""
focus_date: ""
priority:
  - High
estimate:
depends_on: []
related: []
github_type:
  - github_issue
github_repo: mypl_spec
github_id: Issue#85
github_url: https://github.com/FutureLinkNetwork/mypl_spec/issues/85
github_updated_at: 2026-10-09T00:10:18Z
backlog_id: MYPL-4236
backlog_url: https://fln2000.backlog.com/view/MYPL-4236  # pragma: allowlist secret
backlog_updated_at: 2026-11-13T08:23:59Z
---
## 概要

dev が本番 analyzer を向いて GBP に誤投稿した件の再発防止として、yaml 管理外の手動ジョブを棚卸しし、yaml に移すか削除する。10/14 の週に実施。

Google Chat「サービス開発室と営業企画×エンジニア陣」再発防止スレッド（10/7）。

GitHub Issue: https://github.com/FutureLinkNetwork/mypl_spec/issues/85

## やったこと

- 10/7 に該当ジョブを停止済み。
- pro のジョブは使用していないため削除した（2026-11-13）。
- sys2 のジョブは動作しており、現在 sys2 全体で yaml 管理を行っていないため、対応なしとした。
- 調査の結果、対応の必要性が無いと判断。問題なければクローズ依頼（加藤優志へ、2026-11-13）。

## 残りのやること