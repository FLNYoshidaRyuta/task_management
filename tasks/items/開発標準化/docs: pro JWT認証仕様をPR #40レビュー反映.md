---
task_id: 88
title: "docs: pro JWT認証仕様をPR #40レビュー反映"
project: 開発標準化
status:
  - todo
start: ""
end: ""
focus_date: ""
priority: []
estimate:
depends_on: []
related: []
github_type:
  - github_pr
github_repo: mypl_microservices_spec
github_id: PR#47
github_url: https://github.com/FutureLinkNetwork/mypl_microservices_spec/pull/47
github_updated_at: 2026-10-15T05:09:26Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

PR #40 のレビューで確定した方針を pro の JWT 認証仕様・処理フロー・手動テスト仕様に反映する。JWT 認証を auth ミドルウェアに集約し公開ページではトークン検証を行わない旨、未ログイン POST は GET /login?origin= 経由に統一、origin はコールバック URL のクエリに載せる、リフレッシュトークンのローテーション無効に合わせた Cookie 更新、旧ログイン入口ルート削除、/api/v1 運営者 API を対象外とする記述、手動テスト仕様の更新。仕様書の更新のみで手動テストは未実施。Refs #38。

## やったこと

## 残りのやること
