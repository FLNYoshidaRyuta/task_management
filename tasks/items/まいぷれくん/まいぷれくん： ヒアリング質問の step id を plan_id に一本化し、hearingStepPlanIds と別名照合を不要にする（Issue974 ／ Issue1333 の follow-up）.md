---
task_id: 17
title: まいぷれくん： ヒアリング質問の step id を plan_id に一本化し、hearingStepPlanIds と別名照合を不要にする（Issue974
  ／ Issue1333 の follow-up）
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
github_id: Issue#1336
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1336
github_updated_at: 2026-10-02 02:30:30+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

まいぷれくんのヒアリング質問には、同じ質問を指す ID が 2 通りある。

- **plan_id**（Agent が振る）: `plan-hearing-q1`。セッション内で一意で、Agent の質問台帳（registry）のキー。
- **step id**（FE が作る）: `plan-hearing-q1:<question_id または質問文>`。`unifiedPostWizardHelpers.ts` の `hearingQuestionKey` が、画面部品のキーとして組み立てる。

FE は `wizard_projection.hearingStepPlanIds`（`{step id → plan_id}`）で両者を行き来している。

step id の合成は 6/20 の FE 統合（ef2102237）で入った。当時は plan_id が LLM 由来で質問ごとに一意の保証がなかったため。7/10 の agent-dev dbe0b15 で Agent が `plan-hearing-qN` を一意に振るようになってからは、plan_id 単独で一意になっている。

この二重表現が原因で、#974 の不具合が起きた（hotfix #1333）。対応表 `hearingStepPlanIds` が rewind/復元で失われると、FE は step id を plan_id として送る。Pro と Agent で正規化の扱いが違うため、material_sources の照合が失敗した。#1333 は次の 2 点で対症療法した。

- 対応表をキー付きで保つ
- Pro が別名でも出典を出す

二重表現そのものは残っている。

## やったこと

ヒアリング質問の step id を plan_id そのものに一本化し、`hearingStepPlanIds` と別名の扱いを不要にする。

- [ ] `hearingQuestionKey` を、plan_id があれば plan_id そのものを返す形にする（plan_id が無い場合の扱いを決める）
- [ ] `questionAnswers` など step id をキーにしている FE 状態・`wizard_projection` の影響範囲を洗い出す
- [ ] 古い形（composite の step id、list 化された `hearingStepPlanIds`）で保存された checkpoint を復元するときの互換
- [ ] `hearingStepPlanIds` の廃止（または互換のための読み取り専用化）
- [ ] 整理後に、Pro の別名照合（`MaterialSourceResolver::questionAnswerPlanIdAliases` / `questionAnswerText`）と Agent 側の composite 正規化（`_COMPOSITE_ID_PATTERN`）を残すか外すか判断する
- [ ] plan_id の正規化を Pro と Agent のどちらか一方に寄せる（ADR-20261001-myplkun-material-sources-plan-id-aliases の follow-up）
- [ ] rewind / リロード復元をまたいだ回帰テスト（実データ形）

## 残りのやること

ヒアリング質問の step id を plan_id そのものに一本化し、`hearingStepPlanIds` と別名の扱いを不要にする。

- [ ] `hearingQuestionKey` を、plan_id があれば plan_id そのものを返す形にする（plan_id が無い場合の扱いを決める）
- [ ] `questionAnswers` など step id をキーにしている FE 状態・`wizard_projection` の影響範囲を洗い出す
- [ ] 古い形（composite の step id、list 化された `hearingStepPlanIds`）で保存された checkpoint を復元するときの互換
- [ ] `hearingStepPlanIds` の廃止（または互換のための読み取り専用化）
- [ ] 整理後に、Pro の別名照合（`MaterialSourceResolver::questionAnswerPlanIdAliases` / `questionAnswerText`）と Agent 側の composite 正規化（`_COMPOSITE_ID_PATTERN`）を残すか外すか判断する
- [ ] plan_id の正規化を Pro と Agent のどちらか一方に寄せる（ADR-20261001-myplkun-material-sources-plan-id-aliases の follow-up）
- [ ] rewind / リロード復元をまたいだ回帰テスト（実データ形）
