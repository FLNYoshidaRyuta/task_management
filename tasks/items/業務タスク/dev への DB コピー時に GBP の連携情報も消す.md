---
task_id: 70
title: dev への DB コピー時に GBP の連携情報も消す
project: 業務タスク
status:
  - in_progress
start: ""
end: ""
focus_date: 2026-10-15
priority:
  - High
estimate:
depends_on: []
related: []
github_type:
  - github_issue
github_repo: mypl-rds-masking
github_id: Issue#7
github_url: https://github.com/FutureLinkNetwork/mypl-rds-masking/issues/7
github_updated_at: 2026-10-16T01:33:50Z
backlog_id: MYPL-4235
backlog_url: https://fln2000.backlog.com/view/MYPL-4235
backlog_updated_at: 2026-10-07T12:50:26Z
---
## 概要

- dev の手動登録ジョブ「DEV PRO / 予約投稿処理」が本番 analyzer を向い Pro dev から本番コピーのニュースを本番 GBP に投稿していた（8/27〜10/7、実店舗32件、10/7停止）。詳細: https://html-review-viewer-775786924346.asia-northeast1.run.app/p/vogd4noiu6/
- 再発防止方針は Google Chat「サービス開発室と営業企画×エンジニア陣」スレッド（10/7）で合意
- インスタは db_masking.sh でアクセストークン全削除のため影響なし。GBP 連携は残っていたため dev から実店舗 GBP に送れる状態だった
- 対象テーブル候補（コメント）: アナライザー→GBP `アナライザーDB.gmb_locations.name`、まいぷれ→アナライザー `mp2.SHOP_BASE2.BASE2_GMB_STATUS`
- 2026-10-16 コメント: 店舗特有エラーの調査・テストのため biz から GBP 接続できる方がよい。可能なら GBP 連携先の削除・マスキングはしない方針。代案は biz 用 GBP 連携アカウントを用意しまいぷれ BASE にのみ招待（各店舗 GBP 権限なし）。店舗特有エラーは店舗のテスト許可と GBP ユーザー招待でテスト

## やったこと

## 残りのやること

- 方針確定後: マスキング SQL への GBP 連携テーブル追加、またはマスキングしない方針・biz 用アカウント案の実装・確認
- 対象テーブル・カラムの確認
- 完了条件: コピー後 dev で GBP 連携店舗 0件（検証店舗は Pro 許可リスト）— 方針変更時はコメントの代案に沿った安全策
