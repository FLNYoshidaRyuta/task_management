---
task_id: 6
title: CMYK画像のアップロード前変換・422エラー文言改善・容量上限の整合性確認
project: 画質向上
start: ''
end: ''
estimate: null
priority: []
status:
- done
depends_on: []
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#1237
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/1237
github_updated_at: '2026-09-16T09:22:38Z'
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

CMYK画像のアップロード前変換・422エラー文言改善・容量上限の整合性確認

## やったこと

- POST /news/357113/image → 422
- POST /shop/357113/myplkun/material-upload → 422
- 対象: line_oa_chat_260908_165043.jpg
- 実ファイル: JPEG、1723×1149px、2,112,601 bytes
- PHP getimagesizefromstring() で channels=4（CMYK）を確認
- 共通のアップロード前処理へ変換を組み込み、ニュース・まいぷれくんなどへの適用範囲を確認する。
- 変換できない場合は原因と次の操作を示し、同じ画像を選び直しても解決しないエラーで単に選び直しを促さない。
- フロント・アプリ・PHP・Webサーバーの容量上限を整合させ、容量超過の案内も改善する。
- [ ] 対象相当のCMYK JPEG（3000px未満・8MiB未満）がニュースとまいぷれくんでアップロードできる。
- [ ] 共通処理を使う他画面への適用範囲を確認する。
- [ ] RGB画像・透過画像・既存のHEIC変換やリサイズを損なわない。
- [ ] 色味・EXIF方向・画質とスマートフォン/WebViewでのメモリ負荷を確認する。

## 残りのやること

- POST /news/357113/image → 422
- POST /shop/357113/myplkun/material-upload → 422
- 対象: line_oa_chat_260908_165043.jpg
- 実ファイル: JPEG、1723×1149px、2,112,601 bytes
- PHP getimagesizefromstring() で channels=4（CMYK）を確認
- 共通のアップロード前処理へ変換を組み込み、ニュース・まいぷれくんなどへの適用範囲を確認する。
- 変換できない場合は原因と次の操作を示し、同じ画像を選び直しても解決しないエラーで単に選び直しを促さない。
- フロント・アプリ・PHP・Webサーバーの容量上限を整合させ、容量超過の案内も改善する。
- [ ] 対象相当のCMYK JPEG（3000px未満・8MiB未満）がニュースとまいぷれくんでアップロードできる。
- [ ] 共通処理を使う他画面への適用範囲を確認する。
- [ ] RGB画像・透過画像・既存のHEIC変換やリサイズを損なわない。
- [ ] 色味・EXIF方向・画質とスマートフォン/WebViewでのメモリ負荷を確認する。
