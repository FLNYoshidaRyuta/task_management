---
task_id: 20
title: 参考画像／投稿素材（material_context.purpose）の分類を廃止するか判断する
project: まいぷれくん
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#946
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/946
github_updated_at: 2026-09-27 10:16:11+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

まいぷれくんの添付画像にある `material_context.purpose`（`post_material` = 投稿素材 / `reference_only` = 参考のみ）の分類を**維持するか廃止するか**を決める。

## やったこと

- Pro は revise 時の添付を正しく `purpose: reference_only` として送る（`src/resources/js/Pages/Myplkun/hooks/useAgentChatSend.ts:280-283`）
- agent は非空の `reference_only` な `material_context` を投稿スロット候補から除外する（`agent-poc/src/runtime/uploaded_image_refs.py:249-251`。ADR-20260729 の実装）
- **しかし agent はその後 `action_payload.material_refs` へフォールバックして無ゲートで採用する**（同 `:252-259`）
- **Pro は revise 時の `action_payload` へ、ウィザードの全 `photoAttachments`（＝いま添付した参考画像を含む）を展開している**（`src/resources/js/Pages/Myplkun/agentChatAttachmentSend.ts:417-445`）
- 投稿作成モード: 上記1により元から素通し
- 相談モード: #934 が「相談モードの画像はそのまま投稿に使う」と決めたため、意図的に素通しにする
- `provenance.attached_mode` を checkpoint 境界へ永続化する処理（`ProComposedCheckpointV2Builder`）
- 昇格判定の二層防御（event allowlist + provenance 判定）と `PostMaterialCarryover` の大部分
- 混在 provenance の fail-closed 規則
- PHP / TypeScript に二重化した添付モード allowlist（`PostMaterialCarryover` と `imageSlots.ts` の `POST_IMAGE_ATTACHED_MODES`）
- **agent-dev の契約変更**（`material_context.purpose` の意味変更または廃止）
- **ADR-20260729 の撤回**（agent-dev `docs/adr/ADR-20260729-reference_only画像はスロットキャッシュへ採用せず空配列クリアだけ維持する.md`）

## 残りのやること

- Pro は revise 時の添付を正しく `purpose: reference_only` として送る（`src/resources/js/Pages/Myplkun/hooks/useAgentChatSend.ts:280-283`）
- agent は非空の `reference_only` な `material_context` を投稿スロット候補から除外する（`agent-poc/src/runtime/uploaded_image_refs.py:249-251`。ADR-20260729 の実装）
- **しかし agent はその後 `action_payload.material_refs` へフォールバックして無ゲートで採用する**（同 `:252-259`）
- **Pro は revise 時の `action_payload` へ、ウィザードの全 `photoAttachments`（＝いま添付した参考画像を含む）を展開している**（`src/resources/js/Pages/Myplkun/agentChatAttachmentSend.ts:417-445`）
- 投稿作成モード: 上記1により元から素通し
- 相談モード: #934 が「相談モードの画像はそのまま投稿に使う」と決めたため、意図的に素通しにする
- `provenance.attached_mode` を checkpoint 境界へ永続化する処理（`ProComposedCheckpointV2Builder`）
- 昇格判定の二層防御（event allowlist + provenance 判定）と `PostMaterialCarryover` の大部分
- 混在 provenance の fail-closed 規則
- PHP / TypeScript に二重化した添付モード allowlist（`PostMaterialCarryover` と `imageSlots.ts` の `POST_IMAGE_ATTACHED_MODES`）
- **agent-dev の契約変更**（`material_context.purpose` の意味変更または廃止）
- **ADR-20260729 の撤回**（agent-dev `docs/adr/ADR-20260729-reference_only画像はスロットキャッシュへ採用せず空配列クリアだけ維持する.md`）
