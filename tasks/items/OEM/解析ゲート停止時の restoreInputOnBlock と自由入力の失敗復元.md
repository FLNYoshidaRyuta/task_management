---
task_id: 91
title: 解析ゲート停止時の restoreInputOnBlock と自由入力の失敗復元
project: OEM
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
github_repo: business-console-pro
github_id: PR#691
github_url: https://github.com/FutureLinkNetwork/business-console-pro/pull/691
github_updated_at: 2026-10-15T13:18:57Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

親: #667 / #678（スタック先: 投稿素材の解析ゲート PR）。解析ゲートで止まったとき、および `restoreInputOnBlock` 付きの自由入力送信では利用者が打った本文を入力欄へ戻す。汎用自由入力の stream `failure` / `stale` 時の空欄復元（#678）も含む。

## やったこと

- `SendMessageOptions.restoreInputOnBlock` と `sendMessage` 内の `setInput`
- `handleSubmitFreeInput` / プレビュー修正の呼び出し箇所へフラグ付与
- `mergeLatestPhotoAnalysisIntoProjection` でゲート失敗時の wizard 復元に最新解析を残す
- ADR・`docs/mypl_pro_diff/20261015_material_analysis_send_gate.md`
- Vitest（`useAgentChatSend.test.ts`）
- テスト 62 passed（vitest run agentChatAttachmentSend.test.ts と useAgentChatSend.test.ts）

## 残りのやること

- ドラフト PR #687（main 向け）は本スタックに取り込んだため、マージ時は #687 を閉じるか本 PR へ差し替える
