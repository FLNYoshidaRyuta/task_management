---
task_id: 38
title: unified_post： legacy撤去後にヒアリングオーケストレーションの責務を整理する
project: agent-poc
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
github_repo: agent-dev
github_id: Issue#282
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/282
github_updated_at: 2026-09-16 15:24:39+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

`unified_post`のヒアリング処理に集中している責務を、legacy経路の撤去後に整理する。

単に巨大関数を別ファイルへ移すのではなく、raw/legacyの二重経路を先に削除し、状態判定・状態更新・生成準備の判断元をそれぞれ一つにする。

## やったこと

- `_shop_agent_confirm_intent_stream`: 約1,177行 / 135分岐
- 内部の`_resolve_next_state`: 約641行 / 90分岐
- raw evidence経路の運用確認が完了している
- `UNIFIED_POST_RAW_EVIDENCE_ENABLED=OFF`への切り戻しが不要と判断されている
- legacy `requirements_plan` writerとreaderの撤去範囲が確定している
- PR #269を含む後続変更との統合が完了している
- 当該ターンの入力・証拠の準備
- judge結果から次状態を決める純粋な判定
- session / journey / registryの状態更新
- 本文生成入力の準備
- stream送出などの副作用
- raw/legacyの二重経路と、不要になったfeature flag分岐が削除されている

## 残りのやること

- `_shop_agent_confirm_intent_stream`: 約1,177行 / 135分岐
- 内部の`_resolve_next_state`: 約641行 / 90分岐
- raw evidence経路の運用確認が完了している
- `UNIFIED_POST_RAW_EVIDENCE_ENABLED=OFF`への切り戻しが不要と判断されている
- legacy `requirements_plan` writerとreaderの撤去範囲が確定している
- PR #269を含む後続変更との統合が完了している
- 当該ターンの入力・証拠の準備
- judge結果から次状態を決める純粋な判定
- session / journey / registryの状態更新
- 本文生成入力の準備
- stream送出などの副作用
- raw/legacyの二重経路と、不要になったfeature flag分岐が削除されている
