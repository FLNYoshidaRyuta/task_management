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
github_updated_at: 2026-10-19T01:13:20Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

Closes #469。`cp .env.example .env` のあと `OPENAI_API_KEY` と `GEMINI_API_KEY` を入れるだけでローカル開発を始められるよう、`agent-poc/.env.example` を日本語化・整理した。

【必須】シークレット、【ローカル標準】そのまま使える値、【任意】必要時のみコメント解除の 3 区分。`UNIFIED_POST_REASONING_EFFORT=low` を有効化（本番推奨構成 ADR-20260729 に合わせる）。`MATERIAL_VISION_IMAGE_SOURCE` と `AGENT_TEXT_ROLLOUT` の説明を実装に合わせて修正。既存 `.env` への影響なし（キー・値の機械比較で同一確認）。

## やったこと

- 英語コメントの日本語化、区分整理、コメントアウト項目の理由表（`AGENT_HEARING_JUDGE_MODEL_CONFIRM`、ルート別 provider 上書き群、`AGENT_REASONING_EFFORT`、`CUSTOM_MEDIA_*` など）。
- `tests/test_mode_config.py` と `tests/test_invocation_observation.py` で 117 tests passed。
- コメントで各任意 env について、本番未設定・コードのフォールバック既定値・値を入れれば上書きできる用途の認識を整理（ローカルでは基本的に未設定のまま、規定値上書きのテスト時のみ使用）。
- レビューコメント（yushi-kato、2026-10-14）で環境変数の経緯を補足。
  - `AGENT_HEARING_JUDGE_MODEL_CONFIRM`: 2026-09-11 に確認型店舗のヒアリング判定だけ gpt-5.1 に切り替え可能にした例外設定。コードだけでは変わらず ECS で設定。dev のみ設定、本番未設定。ローカルは未設定が正しい。
  - `AGENT_PROVIDER` 系: 2026-09-03 の提供元切替（OpenAI/Gemini）。ルート別上書きと `AGENT_TEXT_ROLLOUT`。未設定なら OpenAI＋`AGENT_MODEL`。
  - `CUSTOM_MEDIA_*`: 2026-09-02 から有効な独自媒体の文字数対策。既定値で動作。env はデプロイせず数値調整用。`.env.example` の値は既定と同じなのでコメントアウト。
- レビューコメント（yushi-kato、2026-10-19）で本番設定を訂正・整理。
  - `AGENT_HEARING_JUDGE_MODEL_CONFIRM`: 本番未設定。ヒアリング判定は `AGENT_MODEL`（gpt-5.6-luna）。
  - `CUSTOM_MEDIA_*`: 本番未設定。コード既定値で動作。
  - `AGENT_<ROUTE>_*` / `AGENT_TEXT_ROLLOUT`: 本番に設定あり。投稿下書き・修正、チャット、口コミ返信、メール・DM 返信は gemini-3.8-flash。判定系は gpt-5.6-luna。
  - `.env.example`（ローカル）は「基本未設定・上書きテスト時のみ」という整理。本番の値とは別物として見る前提。
- レビューコメント（yushi-kato、2026-10-19）: dev にだけ `AGENT_HEARING_JUDGE_MODEL_CONFIRM` がある理由は検証中。#473（確認型ヒアリング口調見直しと gpt-6-luna 対応）を dev で検証。値は gpt-6-luna。10/21 リリース予定。本番コードは gpt-6-luna 未対応のため env を先に入れられない。リリース見送りなら dev から env を外す。
- コメント（FLNYoshidaRyuta、2026-10-19）: dev 検証中の状況は理解した。

## 残りのやること

- PR レビュー・マージ。
- 本番と同じ非シークレット値を `.env.example` に反映する対応（PR/Issue スレッド上の依頼）。
- #473 のリリースと dev env の扱いは ECS 側の話。リリース見送り時の dev から env を外すなど、必要ならフォロー。
