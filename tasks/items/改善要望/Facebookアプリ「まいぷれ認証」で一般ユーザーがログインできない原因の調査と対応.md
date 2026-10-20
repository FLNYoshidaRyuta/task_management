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
- todo
depends_on: []
github_type: []
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4158
backlog_url: https://fln2000.backlog.com/view/MYPL-4158  # pragma: allowlist secret
backlog_updated_at: '2026-10-20T00:41:02Z'
---
## 概要

SSO（Cognito経由のFacebookログイン）の実装自体は完了しているが、現在は**Facebookアプリにロール（管理者・開発者・テスター）登録された人しか認証できない**状態になっている。
コード側の問題ではなく、Facebook（Meta）側のアプリ設定・申請の問題である。

Facebookアプリの設定項目を調査し、一般のFacebookユーザーがログインできる状態にするために必要な設定・申請を完了させてほしい。

### 対象のFacebookアプリ

- **アプリ名: `まいぷれ認証`**（App ID: `258691954284386`。agora＝旧公開サイトが本番で使ってきた既存アプリ）
- 現在、Cognito の Facebook Identity Provider は全環境でこのアプリを使用している

**新しいFacebookアプリを作って置き換える対応は不可。** FacebookのユーザーID（sub）はアプリごとに別の値が払い出される（app-scoped ID）ため、アプリを変えると既存Facebook連携ユーザーの突合キー（`Facebook_{sns_uid}`）が全員分ズレて重複アカウント化し、復旧不能になる。必ずこのアプリ自体を直すこと。

### 現状わかっていること

- Metaの Facebook Login permission には **Standard Access / Advanced Access** の2段階があり、**Standard Access のままだとアプリのロール保有者しかログインできない**。一般ユーザー全員がログインできるようにするには `public_profile`・`email` を Advanced Access にする必要がある（2026-05-11調査済み）
- 【未実証】「実装直後は動いていたのに今は動かない」原因の特定はできていない。Metaのアクセスレベル制度変更・アプリのモード（Dev Mode / Live Mode）変更・要件未達による機能制限などが候補。2026-03-18には一般アカウントで「このアプリの詳細について追加アップデート中」という旨のエラーでログインできない事例も観測している。**まずダッシュボードで現状を調査して原因を確定させてほしい**

## やったこと

- 2026-10-20（吉田竜大）: アプリ開発者の Facebook アカウントでログインを試行すると、認証画面が表示された。表示内容は「ログインレビューの申請」であり、「以下のアクセス許可に、Facebookでは使用が許可されていないものがあります」という旨のメッセージと、[レビュー申請](https://developers.facebook.com/apps/258691954284386/app-review/submissions/)へのリンクが含まれていた。

## 残りのやること

Meta for Developers のダッシュボードで一般ユーザーがログインできない原因を調査し、必要な設定・申請を実施する。

- `https://funabashi.mypl.work/` からFacebookログインを試み、アプリにロール登録されていない一般のFacebookアカウントでログインが成功すること
- リダイレクトURIは mypl_auth のURLではなく **Cognitoの idpresponse エンドポイント**（`https://mypl-auth-{環境}.auth.ap-northeast-1.amazoncognito.com/oauth2/idpresponse`）を登録する。既存設定を消さないこと
- App Review の審査は通常数日〜2週間、ビジネス認証も数日〜数週間かかる。
- [App Review submission guide - Meta for Developers](https://developers.facebook.com/docs/resp-plat-initiatives/individual-processes/app-review/submission-guide)
- [Business Verification - Meta for Developers](https://developers.facebook.com/docs/development/release/business-verification/)

