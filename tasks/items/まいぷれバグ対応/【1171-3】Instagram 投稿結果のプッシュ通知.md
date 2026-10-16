---
task_id: 32
title: 【1171-3】Instagram 投稿結果のプッシュ通知
project: まいぷれバグ対応
start: ''
end: ''
estimate: null
priority:
- bug
status:
- todo
depends_on: []
related:
- '[[tasks/items/まいぷれバグ対応/【移植漏れ】ネイティブアプリ向けプッシュ通知・お知らせ連携（mypl3_pro 未移植分）|【移植漏れ】ネイティブアプリ向けプッシュ通知・お知らせ連携（mypl3_pro
  未移植分）]]'
- '[[tasks/items/まいぷれバグ対応/【1171-4】プッシュ経由の既読処理|【1171-4】プッシュ経由の既読処理]]'
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#1179
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1179
github_updated_at: 2026-09-16 07:07:16+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

親 Issue #1171 の移植漏れ一覧 3 番「Instagram 投稿結果のプッシュ通知」を `mypl_pro` へ移植する。

Instagram 投稿の成功・失敗が確定したとき、既存の `FcmNotificationService` でプッシュ用お知らせレコード（`SHOP_CRM_ANNOUNCE_RECORD`）を作成する。実 FCM 配信は別系統バッチが `SYS_APP_PRO` のトークンを参照して行う想定で、本 Issue ではレコード登録までを対象とする。

## やったこと

- [ ] Instagram 即時公開の成功時に、プッシュ用お知らせレコードが 1 件作成される
- [ ] Instagram 即時公開の失敗時に、失敗詳細を含むプッシュ用お知らせレコードが 1 件作成される
- [ ] 予約公開の成功・失敗、24 時間期限切れでも同様にレコードが作成される
- [ ] お知らせ作成失敗でも Instagram 投稿の成功・失敗確定はロールバックされない
- [ ] 関連 Unit テストが追加されている

## 残りのやること

- [ ] Instagram 即時公開の成功時に、プッシュ用お知らせレコードが 1 件作成される
- [ ] Instagram 即時公開の失敗時に、失敗詳細を含むプッシュ用お知らせレコードが 1 件作成される
- [ ] 予約公開の成功・失敗、24 時間期限切れでも同様にレコードが作成される
- [ ] お知らせ作成失敗でも Instagram 投稿の成功・失敗確定はロールバックされない
- [ ] 関連 Unit テストが追加されている
