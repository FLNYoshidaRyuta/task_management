---
task_id: 78
title: docs(agent-poc)： .env.example をローカル開発向けに日本語化・整理する（Issue469）
project: agent-poc
status:
  - todo
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
github_updated_at: 2026-10-14T05:25:25Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

`cp .env.example .env` のあと `OPENAI_API_KEY` と `GEMINI_API_KEY` を入れるだけでローカル開発を始められるよう、`agent-poc/.env.example` を日本語化・整理する（Closes #469）。

## やったこと

- PR: コメントを日本語化し、【必須】・【ローカル標準】・【任意】に区分。`UNIFIED_POST_REASONING_EFFORT=low` を有効化。`MATERIAL_VISION_IMAGE_SOURCE` と `AGENT_TEXT_ROLLOUT` の説明を実装に合わせて修正。コメントアウト項目の理由を表で記載。`tests/test_mode_config.py` と `tests/test_invocation_observation.py` で 117 passed。
- レビューコメント（yushi-kato、2026-10-14）で環境変数の経緯を補足。
  - `AGENT_HEARING_JUDGE_MODEL_CONFIRM`: 2026-09-11 に確認型店舗のヒアリング判定だけ gpt-5.1 に切り替え可能にした例外設定。コードだけでは変わらず ECS で設定。dev のみ設定、本番未設定。ローカルは未設定が正しい。
  - `AGENT_PROVIDER` 系: 2026-09-03 の提供元切替（OpenAI/Gemini）。ルート別上書きと `AGENT_TEXT_ROLLOUT`。未設定なら OpenAI＋`AGENT_MODEL`。
  - `CUSTOM_MEDIA_*`: 2026-09-02 から有効な独自媒体の文字数対策。既定値で動作。env はデプロイせず数値調整用。`.env.example` の値は既定と同じなのでコメントアウト。

## 残りのやること

- 本番未設定・コードは残りフォールバック既定値・値を入れれば上書き可能、という理解の確認と、ローカルでも基本未設定で規定値上書きテスト時のみ使う認識のすり合わせ（2026-10-14 コメント）。
- `AGENT_HEARING_JUDGE_MODEL_CONFIRM` が dev のみに残っている理由（テスト終了後本番リリースが無い場合は削除すべきか）の回答待ち。
