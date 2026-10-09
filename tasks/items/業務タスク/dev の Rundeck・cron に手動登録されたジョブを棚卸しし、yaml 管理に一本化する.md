---
task_id: 69
title: dev の Rundeck・cron に手動登録されたジョブを棚卸しし、yaml 管理に一本化する
project: 業務タスク
status:
  - in_progress
start: ""
end: ""
focus_date: 2026-10-14
priority:
  - High
estimate:
depends_on: []
related: []
github_type:
  - github_issue
github_id: FutureLinkNetwork/mypl_spec#85
github_url: https://github.com/FutureLinkNetwork/mypl_spec/issues/85
github_updated_at: 2026-10-09T00:10:18Z
backlog_id: MYPL-4236
backlog_url: https://fln2000.backlog.com/view/MYPL-4236
backlog_updated_at: 2026-10-08T05:52:59Z
---
## 概要

dev の手動登録ジョブ「DEV PRO / 予約投稿処理」が、パラメータストアの重複で本番 analyzer（analyzer.mypl.net）を向いていた Pro dev から、本番コピーのニュースを本番の Google ビジネスプロフィールに投稿していた（8/27〜10/7、実店舗 32件）。

起点は、yaml 管理への移行前に Instagram の動作確認用に手動登録された「DEV PRO / 予約投稿処理」が、移行時に止められず動き続けていたこと。

- 影響と原因の詳細: https://html-review-viewer-775786924346.asia-northeast1.run.app/p/vogd4noiu6/
- 再発防止の方針（合意）: Google Chat「サービス開発室と営業企画×エンジニア陣」の再発防止スレッド（10/7）

## やったこと

- 10/7 に該当ジョブを停止済み

## 残りのやること

- dev の Rundeck の全プロジェクトと、EC2 の crontab・/etc/cron.d を棚卸しする
- yaml にないジョブは、yaml に移すか削除する
