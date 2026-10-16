---
task_id: 24
title: まいぷれくん： ヒアリングで複数質問が届くと receivedBatchId が255文字を超え会話が422で止まる（本体 mypl_proIssue1298
  の OEM 横展開）
project: OEM
start: ''
end: ''
estimate: null
priority:
- Mid
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: business-console-pro
github_id: Issue#658
github_url: https://github.com/FutureLinkNetwork/business-console-pro/issues/658
github_updated_at: 2026-09-27 09:49:38+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

本体 Pro で見つかった不具合 FutureLinkNetwork/mypl_pro#1298 と同じ作りのコードが、OEM にもあります。

症状: まいぷれくんのヒアリングで、1つのバッチに2問以上の質問が届くと `receivedBatchId` が255文字を超えます。以後、chat-stream がすべて 422（`validation_failed`）になり、会話が止まります。

本体 Pro の修正は FutureLinkNetwork/mypl_pro#1299 です（レビュー待ち）。

## やったこと

- `resources/js/Pages/Myplkun/hooks/useUnifiedPostWizardState.ts:252-253`: `"received:" + stepIds.join('|')` で値を組み立てています。
- `resources/js/Pages/Myplkun/unifiedPostWizardHelpers.ts`: `hearingQuestionKey()` は、`question_id` がない場合に質問文をそのまま step id に使います。
- `app/Http/Requests/Myplkun/SendChatRequest.php:200`: `wizard_projection.questionSteps.*.receivedBatchId` を `max:255` で検証しています。
- `app/Services/Myplkun/Hearing/HearingQuestionStepProjector.php:119-126`: サーバー側でも `'received:'.implode('|', ids)` を作っています。この処理は本体 Pro にはありません。

## 残りのやること

- `resources/js/Pages/Myplkun/hooks/useUnifiedPostWizardState.ts:252-253`: `"received:" + stepIds.join('|')` で値を組み立てています。
- `resources/js/Pages/Myplkun/unifiedPostWizardHelpers.ts`: `hearingQuestionKey()` は、`question_id` がない場合に質問文をそのまま step id に使います。
- `app/Http/Requests/Myplkun/SendChatRequest.php:200`: `wizard_projection.questionSteps.*.receivedBatchId` を `max:255` で検証しています。
- `app/Services/Myplkun/Hearing/HearingQuestionStepProjector.php:119-126`: サーバー側でも `'received:'.implode('|', ids)` を作っています。この処理は本体 Pro にはありません。
