---
task_id: 31
title: 【移植漏れ】ネイティブアプリ向けプッシュ通知・お知らせ連携（mypl3_pro 未移植分）
project: まいぷれバグ対応
start: ''
end: ''
focus_date: null
estimate: null
priority:
- bug
status:
- todo
depends_on: []
related:
- '[[tasks/items/まいぷれバグ対応/【1171-3】Instagram 投稿結果のプッシュ通知|【1171-3】Instagram 投稿結果のプッシュ通知]]'
- '[[tasks/items/まいぷれバグ対応/【1171-4】プッシュ経由の既読処理|【1171-4】プッシュ経由の既読処理]]'
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#1171
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1171
github_updated_at: 2026-09-16 07:07:00+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

`mypl3_pro` から `mypl_pro` への移行において、ネイティブアプリ WebView とサーバー間の送受信処理が一部未移植です。

現状 `mypl_pro` には `AppWebViewDetector` による OS 判定（`app-futurelinkcojp-myplpro-os` / Cookie `app-os`）と Instagram OAuth のアプリ向け画面分岐のみが移植されています。

## やったこと

- `mypl3_pro/src/app/libraries/MyplUtil.php` — `is_app()`（トークン保存）、`setAnnounceReadUser()`、`sendFcm()`
- `mypl3_pro/src/app/controllers/SettingController.php` — `set_push_flg`
- `mypl3_pro/src/app/commands/BatchInstagramPostCommand.php` — Instagram 投稿結果通知
- `mypl3_pro/src/app/controllers/AnnounceController.php` — 端末種別フィルタ、未読数（アプリは `[1,3]`）
- `mypl_pro/src/app/Services/Device/AppWebViewDetector.php`
- `mypl_pro/src/app/Services/Notification/FcmNotificationService.php`（口コミ通知は利用済み）
- `mypl_pro/src/app/Services/Bbs/BbsNotificationService.php`
- [ ] アプリ WebView からのリクエストで FCM トークンが `SYS_APP_PRO` に保存される
- [ ] 設定画面でプッシュ通知 ON/OFF を変更でき、`APP_PRO_PUSH_FLG` が更新される
- [ ] Instagram 投稿の成功・失敗時にプッシュ用お知らせレコードが作成される
- [ ] プッシュ通知のリンク先（ニュース・口コミ等）を開いた際、関連お知らせが既読になる
- [ ] アプリからのお知らせ一覧・未読数が端末種別 `1,3` で正しくフィルタされる

## 残りのやること

- `mypl3_pro/src/app/libraries/MyplUtil.php` — `is_app()`（トークン保存）、`setAnnounceReadUser()`、`sendFcm()`
- `mypl3_pro/src/app/controllers/SettingController.php` — `set_push_flg`
- `mypl3_pro/src/app/commands/BatchInstagramPostCommand.php` — Instagram 投稿結果通知
- `mypl3_pro/src/app/controllers/AnnounceController.php` — 端末種別フィルタ、未読数（アプリは `[1,3]`）
- `mypl_pro/src/app/Services/Device/AppWebViewDetector.php`
- `mypl_pro/src/app/Services/Notification/FcmNotificationService.php`（口コミ通知は利用済み）
- `mypl_pro/src/app/Services/Bbs/BbsNotificationService.php`
- [ ] アプリ WebView からのリクエストで FCM トークンが `SYS_APP_PRO` に保存される
- [ ] 設定画面でプッシュ通知 ON/OFF を変更でき、`APP_PRO_PUSH_FLG` が更新される
- [ ] Instagram 投稿の成功・失敗時にプッシュ用お知らせレコードが作成される
- [ ] プッシュ通知のリンク先（ニュース・口コミ等）を開いた際、関連お知らせが既読になる
- [ ] アプリからのお知らせ一覧・未読数が端末種別 `1,3` で正しくフィルタされる
