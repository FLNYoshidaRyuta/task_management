---
task_id: 46
title: ci： 行数ラチェット・チケット単位テスト禁止・テスト比率ガード（警告のみ・試行）
project: 開発標準化
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
related:
- '[[tasks/items/開発標準化/開発ルール整備： PR テンプレート ／ テスト方針 ／ 行数・テストガード|開発ルール整備： PR テンプレート ／
  テスト方針 ／ 行数・テストガード]]'
- '[[tasks/items/開発標準化/docs： PR テンプレート v2 案とテスト方針案（チーム相談用）|docs： PR テンプレート v2 案とテスト方針案（チーム相談用）]]'
- '[[tasks/items/開発標準化/docs： まいぷれくんリファクタ引き継ぎパック（Phase 3 以降）|docs： まいぷれくんリファクタ引き継ぎパック（Phase
  3 以降）]]'
github_type:
- github_pr
github_repo: mypl_pro
github_id: PR#1228
github_url: https://github.com/FutureLinkNetwork/mypl_pro/pull/1228
github_updated_at: 2026-09-18 00:05:21+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

ルール2（行数ラチェット）/ ルール5（チケット単位テスト禁止）/ ルール6（テスト比率）の3ガードを CI へ追加する。**すべて `continue-on-error: true` の警告のみ運用**で、この PR では merge を一切ブロックしない。

## やったこと

- **対象**: `find src/app -type f -name '*.php'`（493 ファイル）。
- **baseline に載っているファイル**: その行数が上限。**超えたら fail、引き下げのみ可**（ラチェット）。
- **baseline に載っていないファイル**: `800` 行で fail（`>=`）。新規・既存の区別なく同じ天井がかかる。
- フロントの行数ガード（`frontend` job, ADR-0023）と同じ思想を PHP へ広げたもの。ADR-0023 の教訓（1000→1900→2000→3000 の現状追認）から、**エラーメッセージで「上限を上げる」選択肢は案内しない**。
- base sha 時点の baseline と比較し、**値の引き上げ**と**エントリの新規追加**を fail させる。引き下げ・削除は通す。
- PR 本文に `size-baseline-exception: ADR-1234`（`^size-baseline-exception:[[:space:]]*ADR-[0-9]{4}$`）の1行がある場合だけ違反を warning に落とす。
- `git diff --numstat -z <base>...HEAD` を **NUL 区切りで解析**して追加行をパスで分類する。
- **分類表**（上から順に判定し、最初に当たったバケツへ入れる）
- **閾値**: テスト追加行 > 実装追加行 × 3 で fail。実装追加 0 行の PR（削除主体・テストのみ）は skip。
- PR 本文に `## テスト比率の理由` の見出しがあれば通す。
- 同じ分類表をスクリプト冒頭のヘッダコメントにも記載している。
- **(1) whitelist 追記の検出**: whitelist を base sha の版と突き合わせ、**増えた行を1件でも error** にする。これが無いと「チケットテストを足しつつ同じ PR で whitelist にも足す」だけで (2) をすり抜けられる。base に whitelist が無い場合（＝この導入 PR 自身）だけ、一過性の bootstrap として検査を skip する。

## 残りのやること

- **対象**: `find src/app -type f -name '*.php'`（493 ファイル）。
- **baseline に載っているファイル**: その行数が上限。**超えたら fail、引き下げのみ可**（ラチェット）。
- **baseline に載っていないファイル**: `800` 行で fail（`>=`）。新規・既存の区別なく同じ天井がかかる。
- フロントの行数ガード（`frontend` job, ADR-0023）と同じ思想を PHP へ広げたもの。ADR-0023 の教訓（1000→1900→2000→3000 の現状追認）から、**エラーメッセージで「上限を上げる」選択肢は案内しない**。
- base sha 時点の baseline と比較し、**値の引き上げ**と**エントリの新規追加**を fail させる。引き下げ・削除は通す。
- PR 本文に `size-baseline-exception: ADR-1234`（`^size-baseline-exception:[[:space:]]*ADR-[0-9]{4}$`）の1行がある場合だけ違反を warning に落とす。
- `git diff --numstat -z <base>...HEAD` を **NUL 区切りで解析**して追加行をパスで分類する。
- **分類表**（上から順に判定し、最初に当たったバケツへ入れる）
- **閾値**: テスト追加行 > 実装追加行 × 3 で fail。実装追加 0 行の PR（削除主体・テストのみ）は skip。
- PR 本文に `## テスト比率の理由` の見出しがあれば通す。
- 同じ分類表をスクリプト冒頭のヘッダコメントにも記載している。
- **(1) whitelist 追記の検出**: whitelist を base sha の版と突き合わせ、**増えた行を1件でも error** にする。これが無いと「チケットテストを足しつつ同じ PR で whitelist にも足す」だけで (2) をすり抜けられる。base に whitelist が無い場合（＝この導入 PR 自身）だけ、一過性の bootstrap として検査を skip する。
