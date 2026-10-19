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
github_updated_at: 2026-10-19T08:30:43Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

GitHub PR（agent-dev#470）: docs(agent-poc): .env.example をローカル開発向けに日本語化・整理する（#469）。Closes #469。

`cp .env.example .env` のあと、秘匿値（`OPENAI_API_KEY` / `GEMINI_API_KEY` / `OPENROUTER_API_KEY`）を入れるだけで、ローカルが本番と同じ設定で動くよう `agent-poc/.env.example` を整理した。方針（吉田合意、PR コメント 2026-10-19）: 秘匿値と接続先（URL・Host・Redis）以外は本番の値をそのまま書く。本番の値は本番 ECS タスク定義リビジョン 68（2026-10-19、平野さん確認）。

4区分（【必須】手で入れるシークレット、【本番と同じ値】、【ローカル用の接続先】、【任意】本番未設定・試すときだけコメント解除）。本番に沿った route 別 Gemini 設定、`AGENT_TEXT_ROLLOUT=all`、`AGENT_REASONING_EFFORT=low`、fallback / material vision などを反映。2026-10-19 に FLNYoshidaRyuta が「こちらの内容で問題ありません。」と承認済み。

## やったこと

- 英語コメントの日本語化と4区分への並べ替え。手設定は OPENAI / GEMINI / OPENROUTER の3キー。
- 本番 rev 68 に沿った値の反映（route 別 Gemini、`AGENT_TEXT_ROLLOUT=all`、`AGENT_REASONING_EFFORT=low`、`AGENT_FALLBACK_PROVIDER=openrouter`、`MATERIAL_VISION_*` の更新など）。本番にない `FIRST_DB_MCP_BASE_URL` / `AGENT_MCP_TRUST_POLICY` は【任意】へ移動。
- 本番の非秘匿値との突き合わせ、起動時検証、`tests/test_mode_config.py` と `tests/test_invocation_observation.py` で 117 tests passed。codex クロスレビュー指摘2件を反映。
- yushi-kato（2026-10-14）: 各【任意】 env の経緯（`AGENT_HEARING_JUDGE_MODEL_CONFIRM`、ルート別 provider / `AGENT_TEXT_ROLLOUT`、`CUSTOM_MEDIA_*` など）の補足。
- yushi-kato（2026-10-19）: 本番設定の訂正（ヒアリング判定は `AGENT_MODEL`、本番は route 別 Gemini 運用、`AGENT_HEARING_JUDGE_MODEL_CONFIRM` は dev で #473 検証中・10/21 リリース予定後に本番反映または見送り時は dev から削除）。
- FLNYoshidaRyuta（2026-10-19）: シークレット以外は本番と同じ値を `.env.example` に載せる依頼。
- fln-khirano（2026-10-19）: 本番の非秘匿 env 一覧を PR に追記。
- yushi-kato（2026-10-19）: 平野さんから本番 TD rev 68 の値で `.env.example` を修正（11cf0b4）。秘匿と接続先以外は本番値。PR 説明に詳細。
- FLNYoshidaRyuta（2026-10-19T08:30:43Z）: 内容承認。

## 残りのやること

- PR のマージ。
- PR 説明の未検証項目: docker compose での実起動と実 API の呼び出し。
- `AGENT_HEARING_JUDGE_MODEL_CONFIRM` は #473 リリース（10/21 予定）で本番に `gpt-6-luna` を入れたら `.env.example` も同値で有効化する追従が必要（本番未設定のまま）。
