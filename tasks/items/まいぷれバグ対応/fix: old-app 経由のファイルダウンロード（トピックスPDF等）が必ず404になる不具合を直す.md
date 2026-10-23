---
task_id: 107
title: 'fix: old-app 経由のファイルダウンロード（トピックスPDF等）が必ず404になる不具合を直す'
project: まいぷれバグ対応
status:
  - todo
start: ''
end: ''
focus_date: ''
priority: []
estimate:
depends_on: []
related: []
github_type:
  - github_pr
github_repo: mypl_laravel3
github_id: PR#2059
github_url: https://github.com/FutureLinkNetwork/mypl_laravel3/pull/2059
github_updated_at: 2026-10-23T11:02:04Z
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

GitHub PR（mypl_laravel3#2059）: fix: old-app 経由のファイルダウンロード（トピックスPDF等）が必ず404になる不具合を直す。

`mp_backend_enabled=true` でも、公開サイトの `/filedownload/?fd=…&pk=topics`（自治体・トピックスの添付PDF）が、old-app が正しく返していても必ず 404（ER-003200-07）になる。biz で再現例: https://sayama.mypl.biz/filedownload/?fd=465386d0246509d905ab16e85f4516fa&pk=topics。`pk=soka_life_learn` / `mylounge` / `com` 経由も同様。コミュニティの添付（`community/*/download`）も同じ原因で落ちる。

原因は #2052（1c1cf9e）で `file_get_contents` を `MyplCrudBackendDb::backendGet` に置き換えたこと。`$http_response_header` は `file_get_contents` を呼んだ関数の中にしか作られないため、呼び出し元では常に未定義になり、ステータス判定が必ず失敗していた。

修正内容: `backendGet` が直前の応答ヘッダーを `MyplCrudBackendDb::$lastResponseHeaders` に残す（呼ぶたびに最初に空にするので、停止中・接続失敗のときは空）。`FileDownloadController` / `CommunityController` はこのヘッダーでステータスと Content-Type を判定する（判定内容は従来どおり）。他の `backendGet` 呼び出し元（13ファイル）は戻り値の本文しか使っておらず、影響なし。回帰テスト `app/tests/standalone/backend_get_response_headers.php`（組み込みサーバーで 200/404/スイッチOFF を確認し、`backendGet` の呼び出し元が `$http_response_header` を読んでいないか検査）。PHP 7.4 で OK、修正前のコードでは失敗することを確認済み。

確認方法: biz（スイッチ ON）では上記 URL で PDF が開くこと。本番（スイッチ OFF）では `pk` 付きの `/filedownload` とコミュニティ添付は、従来どおりルートのフィルタで「一時停止中」表示のまま（コントローラーまで来ない）。

本番を #2057 で `mp_backend_enabled=true` に戻す前（または同時）に入っている必要がある。biz（stage）での確認用に、同じブランチから stage 向けの PR も出している。

## やったこと

## 残りのやること

