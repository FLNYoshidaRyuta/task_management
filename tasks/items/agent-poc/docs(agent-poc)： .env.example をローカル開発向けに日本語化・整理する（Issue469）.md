---
task_id: 78
title: docs(agent-poc)： .env.example をローカル開発向けに日本語化・整理する（Issue469）
project: agent-poc
status:
  - in_progress
start: ""
end: ""
focus_date: ""
priority:
  - Low
estimate:
depends_on: []
related: []
github_type:
  - github_pr
github_repo: agent-dev
github_id: PR#470
github_url: https://github.com/FutureLinkNetwork/agent-dev/pull/470
github_updated_at: 2026-10-19T06:00:22Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

Closes #469。`cp .env.example .env` のあと `OPENAI_API_KEY` と `GEMINI_API_KEY` を入れるだけでローカル開発を始められるよう、`agent-poc/.env.example` を日本語化・整理した。

【必須】シークレット、【ローカル標準】そのまま使える値、【任意】必要時のみコメント解除の 3 区分。`UNIFIED_POST_REASONING_EFFORT=low` を有効化（本番推奨構成 ADR-20260729 に合わせる）。`MATERIAL_VISION_IMAGE_SOURCE` と `AGENT_TEXT_ROLLOUT` の説明を実装に合わせて修正。既存 `.env` への影響なし（キー・値の機械比較で同一確認）。

PR 説明では、コメントアウトのままにした項目（`AGENT_HEARING_JUDGE_MODEL_CONFIRM`、ルート別 provider 上書き群、`AGENT_REASONING_EFFORT`、`CUSTOM_MEDIA_*` など）の理由を表で整理している。2026-10-19 のスレッドでは、本番の非秘匿 env の実態（ルート別 Gemini 設定など）と、ローカル `.env.example` を本番に近づける追加対応の依頼が出ている。

## やったこと

- 英語コメントの日本語化、区分整理、コメントアウト項目の理由表（`AGENT_HEARING_JUDGE_MODEL_CONFIRM`、ルート別 provider 上書き群、`AGENT_REASONING_EFFORT`、`CUSTOM_MEDIA_*` など）。
- `tests/test_mode_config.py` と `tests/test_invocation_observation.py` で 117 tests passed。
- コメントで各任意 env について、本番未設定・コードのフォールバック既定値・値を入れれば上書きできる用途の認識を整理（ローカルでは基本的に未設定のまま、規定値上書きのテスト時のみ使用）。
- レビューコメント（yushi-kato、2026-10-14）で環境変数の経緯を補足。
  - `AGENT_HEARING_JUDGE_MODEL_CONFIRM`: 2026-09-11 に確認型店舗のヒアリング判定だけ gpt-5.1 に切り替え可能にした例外設定。コードだけでは変わらず ECS で設定。dev のみ設定、本番未設定。ローカルは未設定が正しい。
  - `AGENT_PROVIDER` 系: 2026-09-03 の提供元切替（OpenAI/Gemini）。ルート別上書きと `AGENT_TEXT_ROLLOUT`。未設定なら OpenAI＋`AGENT_MODEL`。
  - `CUSTOM_MEDIA_*`: 2026-09-02 から有効な独自媒体の文字数対策。既定値で動作。env はデプロイせず数値調整用。`.env.example` の値は既定と同じなのでコメントアウト。
- レビューコメント（yushi-kato、2026-10-19）で本番設定の訂正。
  - `AGENT_HEARING_JUDGE_MODEL_CONFIRM`: 本番未設定。ヒアリング判定はすべて `AGENT_MODEL`（gpt-5.6-luna）。
  - `CUSTOM_MEDIA_*`: 本番未設定。コード既定値（1.30 / 140 / 0.10 / 20秒）が効いている。
  - `AGENT_<ROUTE>_*` / `AGENT_TEXT_ROLLOUT`: 本番で設定あり。投稿の下書き作成・修正、チャット、口コミ返信、メール・DM 返信は gemini-3.8-flash。判定系は gpt-5.6-luna。
  - dev の `AGENT_HEARING_JUDGE_MODEL_CONFIRM` は #473 検証中。10/21 リリース予定後に本番にも入れる。見送りなら dev から外す。
- レビューコメント（FLNYoshidaRyuta、2026-10-19）: ローカルは本番に近い設定を期待。シークレット以外で本番に値があるキーは、本番の値を `.env.example` に載せる対応を依頼。
- レビューコメント（fln-khirano、2026-10-19）: 本番の非秘匿 env 一覧を PR に追記（environment 平文と ECS TD/SSM 参照の変数名・値または空欄）。

## 残りのやること

- 本番に値がありシークレットでないキーを、本番の値として `.env.example` に反映する（FLNYoshidaRyuta 依頼。fln-khirano 追記の一覧を参照）。
- PR のレビュー・マージ。
- `AGENT_HEARING_JUDGE_MODEL_CONFIRM` の dev 設定は #473 検証・10/21 リリース後の本番反映、またはリリース見送り時の dev からの削除をフォロー。
