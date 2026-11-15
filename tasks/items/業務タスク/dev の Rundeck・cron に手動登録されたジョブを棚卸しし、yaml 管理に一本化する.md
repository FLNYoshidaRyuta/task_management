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

dev の手動登録ジョブ「DEV PRO / 予約投稿処理」が、パラメータストアの重複で本番 analyzer（analyzer.mypl.net）を向いていた Pro dev から、本番コピーのニュースを本番の Google ビジネスプロフィールに投稿していた（8/27〜10/7、実店舗 32件）。

起点は、yaml 管理への移行前に Instagram の動作確認用に手動登録された「DEV PRO / 予約投稿処理」が、移行時に止められず動き続けていたこと。

Backlog・GitHub 上の課題は、dev 環境の GBP 誤投稿の再発防止と、10/14 週を目安とした Rundeck・cron の手動登録ジョブの棚卸しである。

- 影響と原因の詳細: https://html-review-viewer-775786924346.asia-northeast1.run.app/p/vogd4noiu6/
- 再発防止の方針（合意）: Google Chat「サービス開発室と営業企画×エンジニア陣」の再発防止スレッド（10/7）

## やったこと

- 10/7 に該当ジョブを停止済み
- 2026-11-13: pro プロジェクトのジョブを棚卸しし、未使用のものは削除した。sys2 プロジェクトのジョブは稼働中だが、sys2 全体が yaml 管理対象外のため対応不要と判断した。調査のうえ追加対応は不要と判断し、問題なければ加藤さんにクローズ依頼した（https://github.com/FutureLinkNetwork/mypl_spec/issues/85#issuecomment-6208707892）

## 残りのやること

- Backlog・Issue のクローズは加藤さんの確認待ち