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

Closes #469。`cp .env.example .env` のあと秘匿値（`OPENAI_API_KEY` / `GEMINI_API_KEY` / `OPENROUTER_API_KEY`）を入れるだけで、ローカルが本番と同じ設定で動くよう `agent-poc/.env.example` を整理した。

方針（吉田・加藤合意、2026-10-19 PRコメント）: 秘匿値と接続先（URL・Host・Redis）以外は本番の値をそのまま書く。本番値は本番 ECS タスク定義 rev 68（2026-10-19、平野確認）。

4区分: 【必須】シークレット、【本番と同じ値】、【ローカル用の接続先】、【任意】本番未設定で試すときだけ。

本番にそろえた route 別 Gemini 設定、`AGENT_TEXT_ROLLOUT=all`、`AGENT_REASONING_EFFORT=low`、`AGENT_FALLBACK_PROVIDER=openrouter`、`OPENROUTER_AGENT_MODEL`、MATERIAL_VISION モデル更新、`MATERIAL_VISION_TIMEOUT_SECONDS` 削除など（更新差分の一覧どおり）。`FIRST_DB_MCP_BASE_URL` / `AGENT_MCP_TRUST_POLICY` は【任意】へ移動（本番で未使用）。

## やったこと

- 英語コメント日本語化・4区分整理、`OPENROUTER_API_KEY` 追加。
- 本番 rev68 と機械突合（接続先の `OEM_API_HOST_HEADER` のみ差分、本番にない有効キーはコード既定値と同じ）。
- `.env.example` 読み込み状態の起動時検証（route・`AGENT_TEXT_ROLLOUT`）。
- `tests/test_mode_config.py`, `tests/test_invocation_observation.py` 117 passed。
- codex クロスレビュー指摘2件反映。
- コメントスレッドで環境変数経緯の整理（`AGENT_HEARING_JUDGE_MODEL_CONFIRM` は 2026-09-11 追加の例外設定、dev のみ・本番未設定・#473 検証中；`AGENT_PROVIDER` 系は 2026-09-03 の提供元切替；`CUSTOM_MEDIA_*` は 2026-09-02 から有効な独自媒体文字数対策、既定値で動作）。
- 加藤が 11cf0b4 で本番 TD rev68 に基づき `.env.example` を再修正（2026-10-19）。
- 平野が本番 env 一覧をコメント（2026-10-19）。
- 吉田が PR 内容承認（2026-10-19 08:30）。

## 残りのやること

- PR のレビュー・マージ（吉田承認済みなのでマージ待ち）。
- 未検証: docker compose 実起動・実 API 呼び出し。
- #473 リリース（10/21予定）後、本番に gpt-6-luna を入れたら `AGENT_HEARING_JUDGE_MODEL_CONFIRM` を本番と同じ値で有効化する追従が必要（【任意】表の補足）。
