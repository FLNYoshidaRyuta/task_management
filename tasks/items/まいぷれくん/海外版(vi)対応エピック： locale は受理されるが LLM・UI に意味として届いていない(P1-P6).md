---
task_id: 22
title: 海外版(vi)対応エピック： locale は受理されるが LLM・UI に意味として届いていない(P1-P6)
project: まいぷれくん
start: ''
end: ''
estimate: null
priority:
- bug
status:
- todo
depends_on: []
related:
- '[[tasks/items/まいぷれくん/[改善][まいぷれくん] 保存側ヒアリング fallback 文言が日本語ハードコードで vi 翻訳が使われない|[改善][まいぷれくん]
  保存側ヒアリング fallback 文言が日本語ハードコードで vi 翻訳が使われない]]'
- '[[tasks/items/まいぷれくん/確認カードの見出し（入れたい内容／注目したいポイント）がベトナム語画面でも日本語のまま表示される|確認カードの見出し（入れたい内容／注目したいポイント）がベトナム語画面でも日本語のまま表示される]]'
- '[[tasks/items/まいぷれバグ対応/グループニュースの共有プレビューが日本語固定になる|グループニュースの共有プレビューが日本語固定になる]]'
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#465
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/465
github_updated_at: 2026-09-27 10:16:17+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

海外版(まず vi)対応に向けた 2026-08-21 の監査で、locale の扱いが**「受理」と「消費」の2層で大きく乖離**していることが判明した。

- **受理層(完了)**: Pro は全 agent リクエストに locale を注入する(AgentCommandClient / chat envelope)。agent 側は 62d1611(drop-filter)+ agent-dev#216/PR#217(11モデル明示宣言)で 422 にせず受理する。
- **消費層(ほぼ未着手)**: locale が実際にプロンプト・LLM・出力言語決定に到達するのは **15経路中2つだけ**(`agent_task.qa_create` / `agent_task.external_media_refine`。両者は Language Rule をプロンプトに実装済みで手本になる)。**主機能の chat は受理するが読み出しコードが0行**で、system prompt に言語ルール自体が存在しない。出力言語を決めているのは「プロンプトが日本語で書かれていること」だけで、制御機構は無い。

用語の取り決め: 本エピックでは **「locale 受理」(422にしない・完了)と「locale 消費」(意味として LLM/UI に届く・本エピックの対象)を区別**して扱う。「多言語対応が入った」という要約は受理層のみを指す場合があるため注意。

## やったこと

- **受理層(完了)**: Pro は全 agent リクエストに locale を注入する(AgentCommandClient / chat envelope)。agent 側は 62d1611(drop-filter)+ agent-dev#216/PR#217(11モデル明示宣言)で 422 にせず受理する。
- **消費層(ほぼ未着手)**: locale が実際にプロンプト・LLM・出力言語決定に到達するのは **15経路中2つだけ**(`agent_task.qa_create` / `agent_task.external_media_refine`。両者は Language Rule をプロンプトに実装済みで手本になる)。**主機能の chat は受理するが読み出しコードが0行**で、system prompt に言語ルール自体が存在しない。出力言語を決めているのは「プロンプトが日本語で書かれていること」だけで、制御機構は無い。
- 最初のスライス(P6+P1)は agent-dev 側 issue として起票済み(コメント欄にリンク)。
- 前提: agent-dev PR #217(11モデルの locale 明示宣言)の merge。
- P2 の image_tag は enum 契約の設計判断、P3 は地域前提の見直しを含むため、それぞれ着手時に方針決定を先行させること。
- locale=vi のユーザーで、chat・各 AI 機能の表示文が vi で出力される(構造キー・enum は不変)。
- Pro 画面(少なくとも Myplkun 系導線)が vi 表示になる。
- locale=ja の既存挙動は不変。

## 残りのやること

- **受理層(完了)**: Pro は全 agent リクエストに locale を注入する(AgentCommandClient / chat envelope)。agent 側は 62d1611(drop-filter)+ agent-dev#216/PR#217(11モデル明示宣言)で 422 にせず受理する。
- **消費層(ほぼ未着手)**: locale が実際にプロンプト・LLM・出力言語決定に到達するのは **15経路中2つだけ**(`agent_task.qa_create` / `agent_task.external_media_refine`。両者は Language Rule をプロンプトに実装済みで手本になる)。**主機能の chat は受理するが読み出しコードが0行**で、system prompt に言語ルール自体が存在しない。出力言語を決めているのは「プロンプトが日本語で書かれていること」だけで、制御機構は無い。
- 最初のスライス(P6+P1)は agent-dev 側 issue として起票済み(コメント欄にリンク)。
- 前提: agent-dev PR #217(11モデルの locale 明示宣言)の merge。
- P2 の image_tag は enum 契約の設計判断、P3 は地域前提の見直しを含むため、それぞれ着手時に方針決定を先行させること。
- locale=vi のユーザーで、chat・各 AI 機能の表示文が vi で出力される(構造キー・enum は不変)。
- Pro 画面(少なくとも Myplkun 系導線)が vi 表示になる。
- locale=ja の既存挙動は不変。
