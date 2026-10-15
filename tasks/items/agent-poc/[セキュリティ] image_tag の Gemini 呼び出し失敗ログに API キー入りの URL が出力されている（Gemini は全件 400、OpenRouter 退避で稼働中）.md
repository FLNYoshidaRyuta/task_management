---
task_id: 34
title: "[セキュリティ] image_tag の Gemini 呼び出し失敗ログに API キー入りの URL が出力されている（Gemini は全件 400、OpenRouter 退避で稼働中）"
project: agent-poc
start:
end: ""
focus_date: 2026-10-15
estimate:
priority:
  - bug
status:
  - in_progress
depends_on: []
github_type:
  - github_issue
github_repo: agent-dev
github_id: Issue#455
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/455
github_updated_at: 2026-10-15T06:05:09Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

**現象:** 本番 agent-sdk（CloudWatch `/ecs/production-mypl-agentsdk`）で、`agent-poc/src/services/news_image_ai.py` の `_call_gemini_json()` が `params={"key": api_key}` により Gemini API キーを含む URL がログに出力される。失敗時の `httpx.HTTPStatusError` が traceback ごと記録される。`task=image_tag`（`gemini-3.5-flash-lite`）はすべて 400 で失敗するが OpenRouter 退避でタグ付けは動作している。

**期待:** API キーがログ・例外に出ない。image_tag の Gemini 呼び出しが成功するか primary から外す。失敗理由はキーを含まない形で記録する。

**対応案:** キー再発行、`x-goog-api-key` ヘッダー送信、ログで URL を出さない、`responseSchema` / `responseJsonSchema` 等による 400 原因の調査、同様の `generativelanguage.googleapis.com` 呼び出しの横展開確認。`material_vision_analyzer.py` もクエリ文字列送信のためヘッダー化が望ましい（image_caption は未確認の懸念あり）。

**確認方法:** CloudWatch で `generativelanguage.googleapis.com` かつ `key=` を含むログが修正後 0 件になること。

## やったこと

- `responseSchema` と `responseJsonSchema` の調査。`additionalProperties` を `responseSchema` に載せていることが image_tag の 400 原因。`responseJsonSchema` への切替または `additionalProperties` 除去で 200。API キーは `x-goog-api-key` ヘッダーで送れる。
- agent-dev#460（ヘッダー統一・`responseJsonSchema` 等）マージ後に、新規 Gemini API キー作成・ローカル確認・ステージング設定・ステージング確認・本番反映の手順で進める方針。
- 10/7 リリース後、CloudWatch の `key=` ログは 0 件であることを確認。
- 10/15 コメントでステージングまでの確認完了。新規 API キーを本番 `GEMINI_API_KEY` に設定済み。数日安定後に旧キー削除予定。

## 残りのやること

本番キー差し替え後の安定確認と旧キー削除。Issue が open のままのため、完了条件の確認とクローズ判断。
