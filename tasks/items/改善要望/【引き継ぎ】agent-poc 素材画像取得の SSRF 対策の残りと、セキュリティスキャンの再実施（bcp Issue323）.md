---
task_id: 13
title: 【引き継ぎ】agent-poc 素材画像取得の SSRF 対策の残りと、セキュリティスキャンの再実施（bcp Issue323）
project: 改善要望
status: todo
start:
end:
priority:
estimate:
depends_on: []
related:
  - "[[tasks/items/改善要望/[セキュリティ改善] agent-pocの素材画像取得を安全なURL・容量制限へ変更する|[セキュリティ改善] agent-pocの素材画像取得を安全なURL・容量制限へ変更する]]"
source_type: backlog_issue
source_id: MYPL-4197
source_url: https://fln2000.backlog.com/view/MYPL-4197
source_updated_at: 2026-09-29T11:26:40Z
---
GitHub issue: https://github.com/FutureLinkNetwork/business-console-pro/issues/323
資料（脅威モデル・スキャン結果・境界強化の設計と実装計画・ADR 案）: https://github.com/FutureLinkNetwork/agent-dev/tree/docs/agent-poc-security-threat-model
資料の場所と現状は issue のコメントにまとめています: https://github.com/FutureLinkNetwork/business-console-pro/issues/323#issuecomment-5889014020

内容：
・画像解析で利用者が送った URL を agent-poc が取得できるため、内部 URL や巨大なファイルを取得される余地がある（SSRF）。agent-dev#215 で一部対応済みで、送り先の限定・DNS rebinding 対策・Pro 側の容量上限・runbook などが残っています。
・Codex Security のスキャンは 397 ファイル中 229 ファイルで容量停止した途中結果です。残り 168 ファイルを含めたスキャンのやり直しもお願いします。
・資料は 7 月時点のコードが前提なので、着手時に現行コードとの差分確認をお願いします。

急ぎではありません。
