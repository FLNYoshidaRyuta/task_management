---
task_id: 79
title: docs： proのJWT認証仕様とテスト仕様を追加する
project: 開発標準化
status:
  - todo
start: ""
end: ""
focus_date: ""
priority:
  - Mid
estimate:
depends_on: []
related: []
github_type:
  - github_pr
github_repo: mypl_microservices_spec
github_id: PR#40
github_url: https://github.com/FutureLinkNetwork/mypl_microservices_spec/pull/40
github_updated_at: 2026-10-14T08:45:02Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

まいぷれシステム全体のシングルサインオン化に向け、pro に導入する JSON Web Token 認証の仕様、処理フロー、手動テスト仕様を追加する。共通のシングルサインオンログアウト仕様とテスト仕様へ pro の期待挙動も追記する。pro は Laravel 12＋Inertia＋React の SPA 構成で、ログイン画面へはフルリロードで遷移させる必要がある。Refs #38。

## やったこと

- PR 本文の変更内容（`feature_specifications/mypl_pro/jwt_authentication/` の 01 認証仕様・02 処理フロー図・03 テスト仕様の追加、共通ログアウト仕様・テスト仕様の更新）をドラフトとして記載。仕様書のみのため手動テストは PR 時点では未実施。
- レビュー: sys2 と比較し pro 設計が正しく、sys2 側の修正は #41・#42・#43 に分離。pro は sys2 に合わせる必要はないとのコメント。
- レビュー: sys2 の JS リクエスト認証失敗時の挙動は #45 でタスク化。pro は概ね問題ないが、まいぷれくんのチャット送信や動作記録画面は通信の送り方が異なるため個別確認が必要かもしれない、とのコメント。

## 残りのやること

- 10/9 リリースで pro の main に運営者 API（mypl_pro#1297、`/api/v1` の Bearer トークン認証）が入った。JWT 認証との関係（対象外か切り分け）を確認し仕様に反映する（2026-10-13 定例メモ）。
- 実装後の確認は追加した pro の JWT 認証テスト仕様と共通 SSO ログアウトテスト仕様に沿って行う。まいぷれくん関連の個別確認も含む。
