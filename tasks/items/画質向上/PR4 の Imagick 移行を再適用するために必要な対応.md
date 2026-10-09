---
task_id: 1
title: PR4 の Imagick 移行を再適用するために必要な対応
project: 画質向上
start: ""
end: ""
estimate:
priority:
  - High
status:
  - todo
depends_on: []
github_type:
  - github_issue
github_id: FutureLinkNetwork/089_ImageServer#12
github_url: https://github.com/FutureLinkNetwork/089_ImageServer/issues/12
github_updated_at: ""
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 目的

https://github.com/FutureLinkNetwork/089_ImageServer/pull/4 は、画像エンジンを GD から Imagick に変え、キャッシュディレクトリを `/mnt/extra-disk/temp-image` から `/mnt/extra-disk/temp-image-2026` に変える変更である。この変更でメモリと CPU が逼迫したため、https://github.com/FutureLinkNetwork/089_ImageServer/pull/7 で切り戻し済みである。

この Issue は、#4 の変更を改めて適用するために必要な対応をまとめる。

キャッシュディレクトリを変えると、旧ディレクトリに残っているキャッシュを参照しなくなる。未キャッシュのリクエストが Imagick で一斉に再生成される。Imagick は GD より重く、処理が集中するとメモリと CPU が逼迫する。

キャッシュを一度に作り直さず、参照順を変えて負荷を分散する。

1. 新キャッシュを先に見る
2. 無ければ旧キャッシュを見る
3. それでも無ければ新規に取得する

旧キャッシュが当たるリクエストでは Imagick が走らない。新キャッシュが無い画像だけが徐々に Imagick で生成され、キャッシュが新ディレクトリへ移っていく。

別件として、キャッシュ削除バッチは旧ディレクトリだけを対象に、毎日2時間動いている。削除の日付条件が悪く、実際には1日1回しか動いていない可能性がある。

## 完了条件

- プログラム修正は子タスク「再適用時に新キャッシュを優先し、無ければ旧キャッシュを参照する」の完了とする
- https://github.com/FutureLinkNetwork/089_ImageServer/issues/14 のキャッシュ削除バッチで、新キャッシュディレクトリも削除対象に含める
- キャッシュ削除バッチの日付条件を調査する

## 関連

- 再適用する変更: https://github.com/FutureLinkNetwork/089_ImageServer/pull/4
- 切り戻し: https://github.com/FutureLinkNetwork/089_ImageServer/pull/7
- 子Issue プログラム修正: https://github.com/FutureLinkNetwork/089_ImageServer/issues/13
- 子Issue キャッシュ削除バッチ: https://github.com/FutureLinkNetwork/089_ImageServer/issues/14
