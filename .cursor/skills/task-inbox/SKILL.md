---
name: task-inbox
description: >-
  GitHub と Backlog の取得キャッシュを個人タスクと照合し、タスク化候補を提示する。
  ユーザーが Inbox、未タスクの Issue や課題、外部情報の取り込み、
  新しい仕事候補の確認を頼んだときに使う。タスクファイルは変更しない。
---

# Task Inbox

## Purpose

GitHub と Backlog のキャッシュを個人タスクと照合し、ユーザーがタスク化するものを選べる状態にする。

## Rules

`tasks/items/**` と `tasks/_タスク.md` は変更しない。変更してよいのは task-manager だけ。

タスク化するかはユーザーが決める。優先度、期限、見積もり、完了、project も決めない。

`.env` は読まない。`sources/**` は編集しない。

外部サービスの status、priority、dueDate、estimatedHours を、個人タスクの status、priority、start、end、estimate へコピーしない。

## Procedure

### 1. Fetch

次を実行する。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tasks/_scripts/fetch-github.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tasks/_scripts/fetch-backlog.ps1
```

失敗したソースは照合に使わない。成功したソースだけを次へ渡す。

### 2. Compare

成功したソースだけを指定して実行する。標準出力を分類結果とする。

```powershell
py .\tasks\_scripts\compare_inbox.py --sources github,backlog
```

片方だけ成功したときは、`--sources github` または `--sources backlog` にする。

自分で `sources/**` と `tasks/items/**` を突き合わせて分類しない。

### 3. Present

`linked_tasks` が空の候補だけに番号を付ける。

各新規候補には次を出す。

- 番号
- source_type
- source_id
- title
- source_url
- external_state
- source_updated_at

タイトルだけでは内容が分からないときだけ、キャッシュの本文を短く要約する。キャッシュに無い事実は足さない。

`linked_tasks` があるものは、紐づくタスクをすべてパスで示す。`cache_newer` が true のものは、タスク側とキャッシュ側の更新時刻を並べる。

優先度や、タスク化すべきだという推奨は書かない。

### 4. Wait

ユーザーが番号と project を明示するまで、task-manager を呼ばない。番号だけで project が無いときは、project を聞いて止まる。

タイトルを変える指定が無いときは、キャッシュの title を使う。priority、start、end、estimate の指定が無いときは空欄として渡す。

### 5. Materialize

選ばれた候補だけを task-manager に渡す。

渡す内容は次だけである。

- project
- title
- source_type
- source_id
- source_url
- source_updated_at
- ユーザーが明示した status、priority、start、end、estimate、本文

`source_type` は `backlog_issue`、`github_issue`、`github_pr` のいずれかだけを渡す。渡したあと、task-manager の結果をそのまま報告する。
