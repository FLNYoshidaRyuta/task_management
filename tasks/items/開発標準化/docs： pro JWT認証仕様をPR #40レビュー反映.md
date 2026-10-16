---
task_id: 96
title: 'docs： pro JWT認証仕様をPR #40レビュー反映'
project: 開発標準化
status:
- done
start: ''
end: ''
focus_date: ''
priority: []
estimate: null
depends_on: []
related: []
github_type:
- github_pr
github_repo: mypl_microservices_spec
github_id: PR#47
github_url: https://github.com/FutureLinkNetwork/mypl_microservices_spec/pull/47
github_updated_at: 2026-10-15 05:09:26+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

PR #40 のレビューで確定した方針を pro の JWT 認証仕様・処理フロー・手動テスト仕様に反映する。JWT 認証を auth ミドルウェアに集約し公開ページではトークン検証を行わない旨、未ログイン POST は GET /login?origin= 経由に統一、origin はコールバック URL のクエリに載せる、リフレッシュトークンのローテーション無効に合わせた Cookie 更新、旧ログイン入口ルート削除、/api/v1 運営者 API を対象外とする記述、手動テスト仕様の更新。仕様書の更新のみで手動テストは未実施。Refs #38。

## やったこと

- JWT 認証を `auth` ミドルウェアに集約し、公開ページではトークン検証を行わない旨を記載
- 未ログインの POST は Inertia・JSON・ストリーミングを問わず `GET /login?origin=` 経由に統一
- 戻り先 `origin` は mypl_auth のログイン URL ではなく、コールバック URL のクエリに載せる（sys2 同形）
- リフレッシュトークンのローテーション無効に合わせた Cookie 更新の記述
- 旧ログイン入口のルート削除、`/api/v1` 運営者 API を本仕様の対象外とする記述
- 手動テスト仕様の期待結果・ケースの更新（入口削除確認の削除を含む）

## 残りのやること

- JWT 認証を `auth` ミドルウェアに集約し、公開ページではトークン検証を行わない旨を記載
- 未ログインの POST は Inertia・JSON・ストリーミングを問わず `GET /login?origin=` 経由に統一
- 戻り先 `origin` は mypl_auth のログイン URL ではなく、コールバック URL のクエリに載せる（sys2 同形）
- リフレッシュトークンのローテーション無効に合わせた Cookie 更新の記述
- 旧ログイン入口のルート削除、`/api/v1` 運営者 API を本仕様の対象外とする記述
- 手動テスト仕様の期待結果・ケースの更新（入口削除確認の削除を含む）
