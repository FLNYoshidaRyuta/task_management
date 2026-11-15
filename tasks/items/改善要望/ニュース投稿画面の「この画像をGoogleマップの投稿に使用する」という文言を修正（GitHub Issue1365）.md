---
task_id: 11
title: ニュース投稿画面の「この画像をGoogleマップの投稿に使用する」という文言を修正（GitHub Issue1365）
project: 改善要望
start: ''
end: ''
focus_date: ''
estimate: null
priority:
  - Mid
status:
  - in_progress
depends_on: []
related: []
github_type:
  - github_issue
github_repo: mypl_pro
github_id: Issue#1365
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1365
github_updated_at: 2026-10-14 07:27:59+00:00
backlog_id: MYPL-4222
backlog_url: https://fln2000.backlog.com/view/MYPL-4222  # pragma: allowlist secret
backlog_updated_at: 2026-11-12T02:14:01Z
---
## 概要

ニュース投稿画面の「この画像をGoogleマップの投稿に使用する」という文言には違和感がある。選択できる内容は GBP の「写真」に格納するか否かであり、GBP と Google マップの用語が混在して誤解が生じないよう文言を調整したい。

Backlog（MYPL-4222）では、表示が実体とそろっていないため修正が必要とされている。関連 GitHub Issue: https://github.com/FutureLinkNetwork/mypl_pro/issues/1365

## やったこと

2026-10-14 の Issue コメントで、画面別に GBP・Google マップ・Google ビジネスプロフィールを指す表現の一覧表が共有された（インサイト、オペレーター API、契約、ショップ基本情報、ニュース一覧、ニュース編集、まいぷれくん、マニュアルなどの画面文言）。ニュース編集の「この画像をGoogleマップの投稿に使用する」も表に含まれている。

2026-11-12: 文言統一は工数がかかるため別 Issue を起票した。修正案はデザインガイドラインに沿った表現とした。PR: https://github.com/FutureLinkNetwork/mypl_pro/pull/1590 、別 Issue: https://github.com/FutureLinkNetwork/mypl_pro/issues/1589 。阿部さんが PR を問題なしと確認し、ガイドライン整理は別 Issue に自分をアサインした。

## 残りのやること

- 次回定例リリースに載せる見込み（MYPL-4315）