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
github_updated_at: 2026-10-15T04:19:11Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

本番 agent-sdk（CloudWatch `/ecs/production-mypl-agentsdk`）に、Gemini API キーを含む URL がそのまま出力されている。出力元は `agent-poc/src/services/news_image_ai.py` の `_call_gemini_json()`（`params={"key": api_key}` で失敗時の `httpx.HTTPStatusError` が traceback ごとログに出る）。2026-09-13 以降毎日 150〜670 行（直近7日で約 2,800 行）。`task=image_tag`・モデル `gemini-3.5-flash-lite` はすべて 400 で失敗するが、OpenRouter 退避でタグ付けは動いている（直近3日: Gemini 失敗 1,048 件、OpenRouter でも失敗して `agent task failed: operation=agent_task.image_tag` は 13 件）。

期待: API キーがログ・例外メッセージに出ない。image_tag の Gemini 呼び出しが成功する（または primary から外す）。失敗理由はキーを含まない形で記録する。

## やったこと

- 調査: `responseSchema` に `additionalProperties` を載せていることが 400 の原因。`responseJsonSchema` に載せ替え、または `additionalProperties` を外した `responseSchema` では 200。API キーは `x-goog-api-key` ヘッダーで送れる。
- `material_vision_analyzer.py` の `_analyze_material_ref_gemini()` もクエリ文字列でキーを送っており、同様にヘッダーへ移すべきと整理。
- agent-dev#460（ヘッダー統一・`responseJsonSchema` 等）マージ後にキー再発行と環境反映を行う手順を Issue に記載。
- 10/7 リリース後、Redash（CloudWatch）で `generativelanguage.googleapis.com` かつ `key=` のログは 2026/10/07 08:03 (UTC) が最後で、リリース以降 API キーのログ露出は 0 件と確認。
- キー再発行手順の 1〜4（新規作成、ローカル確認、ステージング環境変数依頼、ステージング動作確認）まで完了（2026-10-15 コメント）。

## 残りのやること

- 手順 5: 問題なければ本番へ適用し、動作確認する（#460 でコード対応済みのため、キー再発行と各環境設定反映が中心）。
- Issue 記載の対応案のうち、本番反映後の Redash クエリでキー露出 0 件の継続確認。
