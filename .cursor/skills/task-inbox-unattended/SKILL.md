---
name: task-inbox-unattended
description: >-
  取得済みの GitHub と Backlog を照合し、新規タスク化と既存タスクの内容更新について
  下書き PR を最大2本作る。同じ種別の open PR があるときは新しい PR を作らない。
  定期実行、無人の Inbox、inbox の下書き PR 作成を頼まれたときに使う。
  対話で候補を選ぶ Inbox では使わない。タスクファイルは task-manager だけが書く。
---

# 無人 Inbox PR

## Purpose

GitHub と Backlog の最新キャッシュを個人タスクと照合し、人間がマージで採否を決める下書き PR を作る。

新規と更新は別 PR にする。候補が無い種別、または同じ候補の open PR がある種別は、PR を作らない。

## Rules

対話で番号を選ぶ手順は `.cursor/skills/task-inbox/SKILL.md` を使う。このスキルではユーザーに確認して止まらない。

タスクファイルと `tasks/_タスク.md` を変えるときは `task-manager` に渡す。このスキルのエージェントが直接編集しない。

`.env` は読まない。`sources/**` は編集もコミットもしない。`tasks/_config/inbox-skipped.json` は変更しない。

優先度、期限、見積もり、完了、外部 Issue や課題の close、タスク化しない判断はしない。`priority`、`start`、`end`、`estimate`、`focus_date` を外部の値から埋めない。`status` は `inbox_pr_guard.py` の JSON に載った `status`（新規）と `status_changes`（更新）だけを `task-manager` に渡す。自分で着手を判断しない。追記候補のポインタ追加、キャッシュに無い未完了タスクの status 変更、`related` と `depends_on` の追加もしない。

新規タスクの project は、この手順のエージェントが既存のタスクツリーを読んで1件ずつ決める。リポジトリ名や Backlog プロジェクトとの対応表は使わない。決めた project を `task-manager` に渡し、`task-manager` は別の project に変えない。

同じ種別の PR を増やすかの判定は `tasks/_scripts/inbox_pr_guard.py` だけが行う。終了コードが 0 でないとき、または標準出力に JSON が無いときは、ファイルも PR も作らず止まる。

取得スクリプトが子プロセスへ渡すトークンで、親の `GH_TOKEN` を上書きしない。PR 一覧はリポジトリの gh 認証で読む。

## Procedure

PowerShell では `py -3`、bash では `python3` を使う。引数は同じにする。失敗したソースは以降に渡さない。両方失敗したときは止まる。

### 1. Fetch

```powershell
py -3 tasks/_scripts/fetch_github.py
py -3 tasks/_scripts/fetch_backlog.py
```

```bash
python3 tasks/_scripts/fetch_github.py
python3 tasks/_scripts/fetch_backlog.py
```

`--refresh-statuses` は付けない。

### 2. Comment prefetch

成功したソースだけを指定する。

```powershell
py -3 tasks/_scripts/fetch_comments.py --sources github,backlog --inbox-updates
```

```bash
python3 tasks/_scripts/fetch_comments.py --sources github,backlog --inbox-updates
```

`cache_newer` の候補が無いときは何もしない。失敗したら、ファイルも PR も作らず止まる。

### 3. Guard

成功したソースだけを指定する。

```powershell
py -3 tasks/_scripts/inbox_pr_guard.py --sources github,backlog
```

```bash
python3 tasks/_scripts/inbox_pr_guard.py --sources github,backlog
```

片方だけ成功したときは `--sources github` または `--sources backlog` にする。

標準出力の JSON を判定の正本にする。`new` と `update` は別々に扱う。`action` は次の3つだけである。

- `skip`: その種別のブランチも PR も作らない。open PR を閉じない。
- `create`: open PR が無い。`origin/main` から新しいブランチを作る。
- `update`: open PR が1本ある。`pr.headRefName` のブランチを更新する。新しい PR は作らない。

`reason` が `unchanged` または `no_candidates` のときは `skip` である。候補の再分類や、マーカーの読み直しをしない。

`attach` と `missing_from_cache` はファイルを変える理由にしない。

### 4. Branch

`create` のブランチ名は `inbox-new-YYYYMMDDHHMM` または `inbox-update-YYYYMMDDHHMM` とする。時刻は UTC の分までとする。

`update` のときは、JSON の `pr.headRefName` を checkout し、`origin/main` をマージしてから差分を載せる。force push はしない。checkout またはマージに失敗したときは、新しいブランチと PR を作らず止まる。

新規ブランチと更新ブランチは、互いをベースにしない。両方とも `origin/main` を起点にする。

### 5. Project

`new.action` が `create` または `update` のときだけ、`new.candidates` の各候補について project を決める。

`tasks/_タスク.md` のタスクツリー見出しと、`tasks/items/` 直下の既存ディレクトリを読む。`routine` は選ばない。候補のタイトルと本文が、既存 project の作業と同じ製品または同じ仕事の流れなら、その project を選ぶ。同じと読めないときだけ、作業内容から新しい project 名を作り、タスクツリーの末尾に見出しを足す。リポジトリ名や Backlog のプロジェクト名を、そのまま project 名にしない。

1候補につきタスクファイルは1件にする。既存タスクの子にはしない。選んだ project と、そう読んだ根拠を PR 本文に書く。

### 6. Materialize

`task-manager` に渡す。

新規候補で渡すものは次だけである。

- 決めた project
- キャッシュの title
- キャッシュの GitHub または Backlog のポインタ
- `status` は、その候補の JSON の `status` だけ（`todo` または `in_progress`）
- `priority` は空、`start`、`end`、`estimate`、`focus_date` は空欄
- 本文は「概要」「やったこと」「残りのやること」の3節。概要には説明欄に書いてある事実だけを書く。事実が無い節は見出しだけにして空にする

新規候補のコメントは取得しない。

`update.action` が `create` または `update` のときは、`cache_newer` の候補について `inbox_hints.py` を実行する。`--update` の値は `source_type:source_id` である。`progress_only` の候補は `inbox_hints.py` に渡さない。

```powershell
py -3 tasks/_scripts/inbox_hints.py --sources github,backlog --update github_issue:owner/repo#12 --update backlog_issue:MYPL-1
```

```bash
python3 tasks/_scripts/inbox_hints.py --sources github,backlog --update github_issue:owner/repo#12 --update backlog_issue:MYPL-1
```

`inbox_hints.py` の `## 更新差分` に書いてある事実だけを使い、`cache_newer` の対象タスクの本文を3節で更新する。当該チャンネルの `github_updated_at` または `backlog_updated_at` をキャッシュの時刻に合わせる。他チャンネルの既存事実は残す。`update.status_changes` にある path だけ `status` を `in_progress` にする。`progress_only` の候補は本文と `*_updated_at` を変えない。外部の state には合わせない。

更新ブランチでは新しいタスクファイルを作らない。新規ブランチでは既存タスクの本文を書き換えない。

この PR のブランチで追加したタスクのうち、今回の `candidates` に無いものは、そのブランチから外す。`origin/main` に既にあるタスクは削除しない。

`task-manager` の操作後スクリプトを、変更したブランチごとに実行する。

```powershell
py -3 tasks/_scripts/generate_routines.py
py -3 tasks/_scripts/assign_task_ids.py
py -3 tasks/_scripts/validate_task_properties.py
py -3 tasks/_scripts/generate_views.py
```

```bash
python3 tasks/_scripts/generate_routines.py
python3 tasks/_scripts/assign_task_ids.py
python3 tasks/_scripts/validate_task_properties.py
python3 tasks/_scripts/generate_views.py
```

### 7. Pull request

差分が無い種別は、commit も push もしない。

差分がある種別だけ、下書き PR にする。ラベルは JSON の `label` を使う。`inbox-new` または `inbox-update` がリポジトリに無いときは、PR を作る前に同じ名前のラベルを作る。

タイトルは新規が `inbox: 新規タスク`、更新が `inbox: 既存タスクの更新` とする。

本文には、各候補の source id、url、変えたタスク path を書く。新規では、選んだ project とその根拠も書く。`new.action` が `skip` のときは、更新 PR の本文に `attach` と `missing_from_cache` を報告として載せる。新規 PR を作るときは、その報告を新規 PR だけに載せる。両方 `skip` のときは、報告のためだけの PR は作らない。

本文の末尾に、JSON の `body_marker` をそのまま1つ置く。文言を変えない。`update` のときは既存 PR の本文をこの内容で置き換える。

push したあと、新しい PR は下書きで開く。既存 PR があるときは、その PR を更新し、2本目を開かない。
