---
task_id: 13
title: 【引き継ぎ】agent-poc 素材画像取得の SSRF 対策の残りと、セキュリティスキャンの再実施（bcp Issue323）
project: 改善要望
start: ""
end: ""
estimate:
priority:
  - Low
status:
  - todo
depends_on: []
related:
  - "[[tasks/items/改善要望/[セキュリティ改善] agent-pocの素材画像取得を安全なURL・容量制限へ変更する|[セキュリティ改善] agent-pocの素材画像取得を安全なURL・容量制限へ変更する]]"
github_type: []
github_id: ""
github_url: ""
github_updated_at: ""
backlog_id: MYPL-4197
backlog_url: https://fln2000.backlog.com/view/MYPL-4197
backlog_updated_at: 2026-09-29T11:26:40Z
---

## 概要

GitHub issue: https://github.com/FutureLinkNetwork/business-console-pro/issues/323
資料（脅威モデル・スキャン結果・境界強化の設計と実装計画・ADR 案）: https://github.com/FutureLinkNetwork/agent-dev/tree/docs/agent-poc-security-threat-model
資料の場所と現状は issue のコメントにまとめています: https://github.com/FutureLinkNetwork/business-console-pro/issues/323#issuecomment-5889014020

画像解析で利用者が送った URL を agent-poc が取得できるため、内部 URL や巨大なファイルを取得される余地がある（SSRF）。

資料は 7 月時点のコードが前提なので、着手時に現行コードとの差分確認が必要。急ぎではない。

## やったこと

- agent-dev#215 で一部対応済み

## 残りのやること

- 送り先の限定
- DNS rebinding 対策
- Pro 側の容量上限
- runbook
- Codex Security のスキャンは 397 ファイル中 229 ファイルで容量停止した途中結果。残り 168 ファイルを含めたスキャンのやり直し
- 着手時に現行コードとの差分確認
