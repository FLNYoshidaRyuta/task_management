---
task_id: 43
title: '[CI-3] main／developを保護し、必須CIが失敗したPRを合流不可にする'
project: 開発標準化
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
github_repo: agent-dev
github_id: Issue#179
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/179
github_updated_at: 2026-09-28 01:23:23+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

2026-08-12時点で `main` / `develop` はどちらも `protected: false` で、repository rulesetもありません。CIが赤でもGitHub上の合流を止める仕組みがない状態です。

## やったこと

- pytest・契約テストのPR Workflowが安定していること
- image smokeが `main` / `develop` 向けPRで安定していること
- 本番デプロイが、同一SHAの品質ゲート成功後だけ進むこと
- codemap checkを必須化する場合、対象外変更でもrequired checkがpendingのままにならないこと
- 複数の個別checkを直接運用判断へ露出させず、PRごとに必ず現れる集約check `quality-gate`（名称は実装時に固定）を必須条件にする
- path対象外の検査は、集約checkへ明示的な `not_applicable` として伝え、永久pendingや黙ったskipを作らない
- まず `develop` へ適用し、成功PR・失敗PR・対象外PRを確認してから `main` へ適用する
- 通常はPR経由を必須とし、force pushとbranch deletionを禁止する
- 緊急bypassは権限者・利用条件・事後記録先を明示し、普段の近道にしない
- 必須checkの正確なcontext名
- `develop` → `main` の適用順と戻し方
- 緊急bypassを持つrole/team

## 残りのやること

- pytest・契約テストのPR Workflowが安定していること
- image smokeが `main` / `develop` 向けPRで安定していること
- 本番デプロイが、同一SHAの品質ゲート成功後だけ進むこと
- codemap checkを必須化する場合、対象外変更でもrequired checkがpendingのままにならないこと
- 複数の個別checkを直接運用判断へ露出させず、PRごとに必ず現れる集約check `quality-gate`（名称は実装時に固定）を必須条件にする
- path対象外の検査は、集約checkへ明示的な `not_applicable` として伝え、永久pendingや黙ったskipを作らない
- まず `develop` へ適用し、成功PR・失敗PR・対象外PRを確認してから `main` へ適用する
- 通常はPR経由を必須とし、force pushとbranch deletionを禁止する
- 緊急bypassは権限者・利用条件・事後記録先を明示し、普段の近道にしない
- 必須checkの正確なcontext名
- `develop` → `main` の適用順と戻し方
- 緊急bypassを持つrole/team
