---
task_id: 117
title: 【設計レビュー】予約機能：着手前レビュー（DDL・ADR・関数の形）
project: 予約機能
status:
- todo
start: ''
end: ''
focus_date:
priority: []
estimate:
depends_on: []
related: []
github_type: []
github_repo: ''
github_id: ''
github_url: ''
github_updated_at: ''
backlog_id: MYPL-4344
backlog_url: https://fln2000.backlog.com/view/MYPL-4344  # pragma: allowlist secret
backlog_updated_at: 2026-11-23T14:51:04Z
---
## 概要

起案者は加藤優志。予約機能の着手前レビューを依頼している。11/27（金）までに各 PR へコメントが欲しい。

予約機能は作る途中でレビューを3回お願いする予定で、今回が1回目（着手前・11/27 まで）。② M1 の節目は 12/18〜12/25 ごろ、③ 実装後（本番前）は 1/12〜1/15 ごろ。

11/9・11/12・11/18 の設計レビューで決めた中身は変えていない。今回新しく決めたのは作る順番で、12月に店の管理画面（pro）の予約画面と予約の仕組み、1月にお客さんの予約画面（公開サイト）と客用API・通知・定期処理を作る。

次の3つを作成した。
1. DDL たたき台（13表）: https://github.com/FutureLinkNetwork/mypl_spec/pull/105
2. DDL の「なぜ」をまとめた ADR 4本: https://github.com/FutureLinkNetwork/mypl_pro/pull/1651
3. 店の画面から呼ぶ関数の形と進め方の1枚: https://github.com/FutureLinkNetwork/mypl_pro/pull/1652（見てほしいコードは `src/app/Services/Booking/` のインターフェースと `Data/` のみ）

進め方の1枚（#1652 の `docs/design/temp/20261123_booking_plan/README.md`）の6章に答えてほしい質問を5つ。GitHub マイルストーン: https://github.com/FutureLinkNetwork/mypl_pro/milestone/4 、https://github.com/FutureLinkNetwork/mypl_spec/milestone/2

## やったこと

## 残りのやること

