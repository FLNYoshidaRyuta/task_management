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
github_updated_at: 2026-10-15T07:05:19Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

まいぷれシステム全体のシングルサインオン化に向け、pro に導入する JSON Web Token 認証の仕様、処理フロー、手動テスト仕様を追加する。共通のシングルサインオンログアウト仕様とテスト仕様へ pro の期待挙動も追記する。pro は Laravel 12＋Inertia＋React の SPA 構成で、ログイン画面へはフルリロードで遷移させる必要がある。追加ドキュメントは `feature_specifications/mypl_pro/jwt_authentication/` の 01 認証仕様・02 処理フロー図・03 テスト仕様と、共通ログアウト仕様の更新（Refs #38）。

## やったこと

- PR 本文の変更内容（`feature_specifications/mypl_pro/jwt_authentication/` の 01 認証仕様・02 処理フロー図・03 テスト仕様の追加、共通ログアウト仕様・テスト仕様の更新）をドラフトとして記載。仕様書のみのため手動テストは PR 時点では未実施。
- sys2 との比較で pro 設計が正しく、sys2 側に直すべき点が 3 件（#41〜#43）と判明。pro はそのままでよい。sys2 の JS リクエスト認証失敗時の挙動は #45 でタスク化。
- まいぷれくんのチャット送信や動作記録画面は通信の送り方が異なるため、実装後に個別確認が必要な可能性がある旨を共有済み。
- 10/9 リリースの運営者 API（mypl_pro#1297、`/api/v1` Bearer 認証）が JWT 仕様に未反映だったため確認・反映依頼。10/15 で仕様に反映。
- レビュー指摘の修正（10/15）: JWT 検証と `PrvUser` セットを `auth` に集約。公開ページはミドルウェアなしでトークン検証・Cookie 削除もしない。例外は `GET /line/link`（`linkToken` あり）と `GET .../myplkun-trace/raw-stream`（未ログインは 401 JSON）。保護ページの GET はログイン画面へリダイレクト、POST（Inertia / JSON / NDJSON）はすべて `GET /login?origin=` へフルページ遷移。旧ログインルートは削除。`/api/v1` は JWT Cookie 対象外（Bearer の運営者 API）。リフレッシュはローテーション無効で ID トークンのみ更新。03 テスト仕様と SSO ログアウト手動テスト（origin / POST 統一 / 公開ページ / リフレッシュ / 運営者 API、先読み・未ログイン URL は sys2 と同粒度）を整理。

## 残りのやること

PR のレビュー・マージ。実装後は 03 テスト仕様と共通 SSO ログアウト手動テストに沿った確認。まいぷれくん関連通信の個別確認。
