---
task_id: 116
title: 【設計レビュー】予約機能：着手前レビュー（DDL・ADR・関数の形）
project: 予約機能
status:
- todo
start: ''
end: ''
focus_date: ''
priority: []
estimate: null
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

起案者：加藤優志。

予約機能の着手前レビューを依頼されている。11/27（金）までに、各 PR にコメントをもらえると助かる。

予約機能は作る途中でレビューを3回お願いする予定で、今回が1回目の①着手前（11/27 まで）。②は M1 の節目（店の画面から予約の作成・変更・取消が通しで動いたところ）で 12/18〜12/25 ごろ。③は実装後（本番に出す前）で 1/12〜1/15 ごろ。

11/9・11/12・11/18 の設計レビューで決めた中身は変えていない。今回新しく決めたのは作る順番で、12月にまず店の管理画面（pro）の予約画面と予約の仕組みを作り、お客さんの予約画面（公開サイト）と客用API・通知・定期処理は1月に作る。

その順番に合わせて次の3つが用意されている。
1. DDL たたき台（13表）: https://github.com/FutureLinkNetwork/mypl_spec/pull/105
2. DDL の「なぜ」をまとめた ADR 4本: https://github.com/FutureLinkNetwork/mypl_pro/pull/1651
3. 店の画面から呼ぶ関数の形と、進め方の1枚: https://github.com/FutureLinkNetwork/mypl_pro/pull/1652（見てほしいコードは `src/app/Services/Booking/` のインターフェースと Data/ のみ。Fake/ やコントローラは仮のもの）

進め方の1枚（#1652 の docs/design/temp/20261123_booking_plan/README.md）の6章に、答えてほしい質問が5つある。特に dev の DB に予約の表を作ってもらう依頼をどなたに出せばよいか（12/11 ごろまでに作ってもらえると助かる）。

M1 は 11/30 から、このたたき台と仮の形で先に始める。返事を待って止めることはせず、指摘をもらったらそこで直す。

GitHub マイルストーン: https://github.com/FutureLinkNetwork/mypl_pro/milestone/4 、 https://github.com/FutureLinkNetwork/mypl_spec/milestone/2

## やったこと


## 残りのやること

