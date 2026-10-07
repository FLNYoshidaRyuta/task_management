---
task_id: 14
title: "[セキュリティ改善] agent-pocの素材画像取得を安全なURL・容量制限へ変更する"
project: 改善要望
status: todo
start:
end:
priority:
estimate:
depends_on: []
related:
  - "[[tasks/items/改善要望/【引き継ぎ】agent-poc 素材画像取得の SSRF 対策の残りと、セキュリティスキャンの再実施（bcp Issue323）|【引き継ぎ】agent-poc 素材画像取得の SSRF 対策の残りと、セキュリティスキャンの再実施（bcp Issue323）]]"
source_type: github_issue
source_id: FutureLinkNetwork/business-console-pro#323
source_url: https://github.com/FutureLinkNetwork/business-console-pro/issues/323
source_updated_at: 2026-09-29T11:08:53Z
---
## 現状と困りごと

初回Codex Security監査 Issue309 で、Business Console Proからagent-pocへ渡した素材画像URLを、agent-pocがdestination検証とresponse byte上限なしでserver-side取得することが確認された。

通常経路ではBusiness Console Proがログインと店舗view権限を確認するが、`material_refs.*.url` は文字数以外のhost／IP制限なくagent-pocへ転送される。agent-pocは任意のhttp(s) URLへGETし、response全体をメモリへ読み込み、`image/*` content-typeならdata URL化して外部vision providerへ渡す。

このままではblind SSRFと、巨大response／data URLによるメモリ・provider費用・可用性への影響が残る。

## 期待する挙動・提案

詳細は GitHub Issue 本文を参照する。

https://github.com/FutureLinkNetwork/business-console-pro/issues/323

## Backlog

https://fln2000.backlog.com/view/MYPL-4197
