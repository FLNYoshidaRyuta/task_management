---
task_id: 76
title: Imagick 移行時に旧キャッシュへフォールバックする
project: 画質向上
status:
- done
start: ''
end: ''
focus_date: ''
priority:
- High
estimate: null
depends_on: []
related: []
github_type:
- github_pr
github_repo: 089_ImageServer
github_id: PR#11
github_url: https://github.com/FutureLinkNetwork/089_ImageServer/pull/11
github_updated_at: 2026-10-13 01:25:42+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

Imagick 化を main に載せたうえで、キャッシュディレクトリ変更による全件再生成を避ける。参照順は新キャッシュ、無ければ旧キャッシュ。新規作成は新ディレクトリのみ。Issue #13 を closes。

## やったこと

- 参照順は新キャッシュ、無ければ旧キャッシュ。サイズが 0 のファイルは未生成として扱います。
- どちらかにあれば、そのファイルを返します。S3 の `file_get_contents`、DB の画像バイナリ、shopn / kos の元画像 HTTP 取得は行いません。
- DB 画像はキャッシュ名に必要な形式と更新日時だけを先に読みます。バイナリは両方のキャッシュが無いときだけ読みます。
- 新規作成、ロック、ディレクトリ作成は `/mnt/extra-disk/temp-image-2026` だけです。旧ディレクトリへは書きません。
- ローカルは `/var/php_tmp/img_cache-2026` と `/var/php_tmp/img_cache` の同じ関係です。
- `php -l` で `index.php`、`db_connect.php`、`fw_imagick.php`、両設定ファイルの構文を確認しました。
- キャッシュパスの解決を PHP で確認しました。新キャッシュ優先、0 バイトは旧キャッシュへフォールバック、旧キャッシュヒット時は新ディレクトリを作らない、ことまで見ています。
- 画像の Imagick 加工と、実サーバーへの配信は未確認です。

## 残りのやること

- 参照順は新キャッシュ、無ければ旧キャッシュ。サイズが 0 のファイルは未生成として扱います。
- どちらかにあれば、そのファイルを返します。S3 の `file_get_contents`、DB の画像バイナリ、shopn / kos の元画像 HTTP 取得は行いません。
- DB 画像はキャッシュ名に必要な形式と更新日時だけを先に読みます。バイナリは両方のキャッシュが無いときだけ読みます。
- 新規作成、ロック、ディレクトリ作成は `/mnt/extra-disk/temp-image-2026` だけです。旧ディレクトリへは書きません。
- ローカルは `/var/php_tmp/img_cache-2026` と `/var/php_tmp/img_cache` の同じ関係です。
- `php -l` で `index.php`、`db_connect.php`、`fw_imagick.php`、両設定ファイルの構文を確認しました。
- キャッシュパスの解決を PHP で確認しました。新キャッシュ優先、0 バイトは旧キャッシュへフォールバック、旧キャッシュヒット時は新ディレクトリを作らない、ことまで見ています。
- 画像の Imagick 加工と、実サーバーへの配信は未確認です。
