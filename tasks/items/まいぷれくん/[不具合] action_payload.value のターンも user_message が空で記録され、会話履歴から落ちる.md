---
task_id: 19
title: '[不具合] action_payload.value のターンも user_message が空で記録され、会話履歴から落ちる'
project: まいぷれくん
start: ''
end: ''
estimate: null
priority:
- bug
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#963
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/963
github_updated_at: 2026-09-27 10:23:26+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

関連: #960（修正指示が会話履歴に残らない）/ 本 issue はその同型で `.value` 系ターンを対象にする

## やったこと

- `user_message.text` が空の行: **10,063件**
- 利用者テキストの実体:
- `action_selected.action_payload.revision_instruction`: **1,095件** → #960 で対処
- `action_selected.action_payload.value`: **6,511件** → **本 issue の対象**
- `revision_instruction`（→ #960）
- `REQUEST_VALIDATION_ERROR` で弾かれるケース（→ #961。別系統）
- 利用者が選んだテーマ名・入力したテキストが `recent_messages` に載り、後続ターンで Agent が参照できる
- Pro が生成した文言（ADR-0053 の残存捏造分）は載らない
- 画面の再読み込み・復元時に、該当ターンの吹き出しが空にならない
- `RECENT_MESSAGES_LIMIT_DEFAULT=20`（#930）の履歴窓の消費増を評価する
- OEM (`business-console-pro`) は `Chat/ChatRequestContextService.php:476-478` で `display_text !== null` をチェックして
- 証跡: orchestrator `reports/lane388/parent-verification-2026-09-02.md`

## 残りのやること

- `user_message.text` が空の行: **10,063件**
- 利用者テキストの実体:
- `action_selected.action_payload.revision_instruction`: **1,095件** → #960 で対処
- `action_selected.action_payload.value`: **6,511件** → **本 issue の対象**
- `revision_instruction`（→ #960）
- `REQUEST_VALIDATION_ERROR` で弾かれるケース（→ #961。別系統）
- 利用者が選んだテーマ名・入力したテキストが `recent_messages` に載り、後続ターンで Agent が参照できる
- Pro が生成した文言（ADR-0053 の残存捏造分）は載らない
- 画面の再読み込み・復元時に、該当ターンの吹き出しが空にならない
- `RECENT_MESSAGES_LIMIT_DEFAULT=20`（#930）の履歴窓の消費増を評価する
- OEM (`business-console-pro`) は `Chat/ChatRequestContextService.php:476-478` で `display_text !== null` をチェックして
- 証跡: orchestrator `reports/lane388/parent-verification-2026-09-02.md`
