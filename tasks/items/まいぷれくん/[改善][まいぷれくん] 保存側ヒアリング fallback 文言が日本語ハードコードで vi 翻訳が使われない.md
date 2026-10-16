---
task_id: 21
title: '[改善][まいぷれくん] 保存側ヒアリング fallback 文言が日本語ハードコードで vi 翻訳が使われない'
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
- '[[tasks/items/まいぷれくん/海外版(vi)対応エピック： locale は受理されるが LLM・UI に意味として届いていない(P1-P6)|海外版(vi)対応エピック：
  locale は受理されるが LLM・UI に意味として届いていない(P1-P6)]]'
- '[[tasks/items/まいぷれくん/確認カードの見出し（入れたい内容／注目したいポイント）がベトナム語画面でも日本語のまま表示される|確認カードの見出し（入れたい内容／注目したいポイント）がベトナム語画面でも日本語のまま表示される]]'
- '[[tasks/items/まいぷれバグ対応/グループニュースの共有プレビューが日本語固定になる|グループニュースの共有プレビューが日本語固定になる]]'
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#986
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/986
github_updated_at: 2026-09-27 10:16:16+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

`app/Services/Myplkun/MyplkunAgentService::extractHearingQuestionTimelineMessage()` は、`display.text` も `intro_text` も無い複数問ヒアリングの保存文言として `'投稿づくりに必要なことをいくつか確認させてください。'` を**日本語リテラル**で返す。`lang/vi/myplkun.php:402`（`confirm.hearing_group_fallback`）にはベトナム語訳があるが保存側では使われないため、vi ロケール店舗で復元・再読込したときだけ日本語が混ざる。

## やったこと

- 保存側の fallback 文言を `__('myplkun.confirm.hearing_group_fallback')` 等の翻訳経由にし、店舗ロケール（`LocaleResolver::fromShop()` 由来）で解決する。
- `MyplkunAgentServiceTest` の該当ケースをロケール別に固定する。
- 起点: #978 の opus レビュー派生候補 3。
- 関連: #978、#465（多言語化エピック）。

## 残りのやること

- 保存側の fallback 文言を `__('myplkun.confirm.hearing_group_fallback')` 等の翻訳経由にし、店舗ロケール（`LocaleResolver::fromShop()` 由来）で解決する。
- `MyplkunAgentServiceTest` の該当ケースをロケール別に固定する。
- 起点: #978 の opus レビュー派生候補 3。
- 関連: #978、#465（多言語化エピック）。
