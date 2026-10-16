---
task_id: 76
title: Imagick 移行時に旧キャッシュへフォールバックする
project: 画質向上
status:
  - done
start: ""
end: ""
focus_date: ""
priority:
  - High
estimate:
depends_on: []
related: []
github_type:
  - github_pr
github_repo: 089_ImageServer
github_id: PR#11
github_url: https://github.com/FutureLinkNetwork/089_ImageServer/pull/11
github_updated_at: 2026-10-13T01:25:42Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

Imagick 化を main に載せたうえで、キャッシュディレクトリ変更による全件再生成を避ける。参照順は新キャッシュ、無ければ旧キャッシュ。新規作成は新ディレクトリのみ。Issue #13 を closes。

## やったこと

## 残りのやること
