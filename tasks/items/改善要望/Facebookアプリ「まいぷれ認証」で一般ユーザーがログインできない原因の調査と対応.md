---
task_id: 15
title: Facebookアプリ「まいぷれ認証」で一般ユーザーがログインできない原因の調査と対応
project: 改善要望
start: ''
end: ''
estimate: null
priority:
- Mid
status:
- in_progress
depends_on: []
github_type: []
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4158
backlog_url: "[REDACTED]/view/MYPL-4158"
backlog_updated_at: '2026-11-10T23:55:36Z'
---
## 概要

SSO（Cognito経由のFacebookログイン）の実装自体は完了しているが、現在は**Facebookアプリにロール（管理者・開発者・テスター）登録された人しか認証できない**状態になっている。
コード側の問題ではなく、Facebook（Meta）側のアプリ設定・申請の問題である。

Facebookアプリの設定項目を調査し、一般のFacebookユーザーがログインできる状態にするために必要な設定・申請を完了させてほしい。

**新しいFacebookアプリを作って置き換える対応は不可。** FacebookのユーザーID（sub）はアプリごとに別の値が払い出される（app-scoped ID）ため、アプリを変えると既存Facebook連携ユーザーの突合キー（`Facebook_{sns_uid}`）が全員分ズレて重複アカウント化し、復旧不能になる。必ずこのアプリ自体を直すこと。

## やったこと

- **アプリ名: `まいぷれ認証`**（App ID: `258691954284386`。agora＝旧公開サイトが本番で使ってきた既存アプリ）
- 現在、Cognito の Facebook Identity Provider は全環境でこのアプリを使用している
- Metaの Facebook Login permission には **Standard Access / Advanced Access** の2段階があり、**Standard Access のままだとアプリのロール保有者しかログインできない**。一般ユーザー全員がログインできるようにするには `public_profile`・`email` を Advanced Access にする必要がある（2026-05-11調査済み）
- 【未実証】「実装直後は動いていたのに今は動かない」原因の特定はできていない。Metaのアクセスレベル制度変更・アプリのモード（Dev Mode / Live Mode）変更・要件未達による機能制限などが候補。2026-03-18には一般アカウントで「このアプリの詳細について追加アップデート中」という旨のエラーでログインできない事例も観測している
- 2026-10-20 吉田竜大コメント: アプリ開発者のFacebookアカウントでログイン試行すると、ログインレビュー申請を促す認証画面が表示された。以下のアクセス許可に、Facebookでは使用が許可されていないものがある旨（`public_profile` 等の使用許可がFacebookで許可されていない）。[レビュー申請](https://developers.facebook.com/apps/258691954284386/app-review/submissions/)へのリンクが表示される
- 2026-10-29 吉田竜大コメント: 現在の仕様では一般ユーザーがアプリを利用するには対象となるアクセス許可の **Advanced Access** の取得が必要。`public_profile`・`email` のアクセス許可は **Standard Access** のまま。Advanced Access を取得するためには、有効なプライバシーポリシーURLおよびデータ削除情報の両方を入力してからリクエストする必要がある。プライバシーポリシーURLは有効なものが設定されている。データ削除情報は無効なものが設定されているため、設定し直しが必要
- 2026-11-02 吉田竜大コメント: データ削除情報は個人情報削除申し立て連絡先があることを根拠にプライバシーポリシーページ（ https://mypl.net/privacy ）を設定した。email アドバンスアクセスを申請し、一度は取得できたが、データアクセスの更新を指示されスタンダードアクセスに戻った。email アドバンスアクセス取得処理の翌日、データアクセスの更新指示通知があったため対応し、現在審査待ち。
- 2026-11-10 吉田竜大コメント: データアクセスの更新が完了した後、アドバンスアクセスに変更し、一般ユーザーでも認証出来た。認証完了後のURLが `https://funabashi.mypl.net//#_=_` となっているため、要修正。

## 残りのやること

- 認証完了後のリダイレクトURLが `https://funabashi.mypl.net//#_=_` となっている問題を修正する（パス末尾の二重スラッシュおよび `#_=_` フラグメント）
- 完了条件: `https://funabashi.mypl.work/` からFacebookログインを試み、アプリにロール登録されていない一般のFacebookアカウントでログインが成功すること（一般ユーザーでの認証は 2026-11-10 時点で成功済み。上記URLの修正後、完了条件どおりの導線でも成功することを確認する）
- リダイレクトURIは mypl_auth のURLではなく **Cognitoの idpresponse エンドポイント**（`https://mypl-auth-{環境}.auth.ap-northeast-1.amazoncognito.com/oauth2/idpresponse`）を登録する。既存設定を消さないこと
- App Review の審査は通常数日〜2週間、ビジネス認証も数日〜数週間かかる
- [App Review submission guide - Meta for Developers](https://developers.facebook.com/docs/resp-plat-initiatives/individual-processes/app-review/submission-guide)
- [Business Verification - Meta for Developers](https://developers.facebook.com/docs/development/release/business-verification/)
