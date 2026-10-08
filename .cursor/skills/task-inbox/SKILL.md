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

照合は各タスクの `source_type` と `source_id` だけを使う。Backlog 課題本文の GitHub URL や、別ソース同士の同一作業は自動判定しない。

個人タスク同士を関連づけるかは Inbox の対象外である。ユーザーが関連だと判断したときは、`task-manager` に指示する。

## Procedure

### 1. Fetch

次を実行する。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tasks/_scripts/fetch-github.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tasks/_scripts/fetch-backlog.ps1
```

Inbox の通常取得では `-RefreshStatuses` を付けない。Backlog の課題は `tasks/_config/backlog-projects.json` と `tasks/_config/backlog-statuses.json` で `include` が `true` のプロジェクトと状態だけが対象になる。`include` が `false` のものは取得キャッシュに出ない。取得結果に無い課題を個人タスクでどうするかは、ユーザーが指示するまで決めない。

失敗したソースは照合に使わない。成功したソースだけを次へ渡す。

### 2. Compare

成功したソースだけを指定して、人向け Markdown を標準出力する。

```powershell
py .\tasks\_scripts\compare_inbox.py --sources github,backlog --format markdown
```

片方だけ成功したときは、`--sources github` または `--sources backlog` にする。

機械処理用に JSON が必要なときだけ `--format json` を使う。既定は `json` だが、Inbox の提示では `markdown` を使う。

自分で `sources/**` と `tasks/items/**` を突き合わせて分類しない。一時的な整形用 Python やテキストファイルを作らない。

### 3. Present

`--format markdown` の出力をそのままユーザーに提示する。内容は次の3セクションである。

- **新規候補**: 番号 `1`, `2`, …（`linked_tasks` が空のキャッシュ項目）
- **更新あり**: 番号 `U1`, `U2`, …（紐づきありかつキャッシュの `source_updated_at` がタスクより新しい）
- **キャッシュに無い未完了タスク**: 番号 `M1`, `M2`, …

各項目に含まれる source_type、source_id、title、url、外部状態、更新日時、紐づくタスク path はスクリプト出力を正とする。エージェントが手で並べ替えや再採番をしない。

タイトルだけでは内容が分からないときだけ、キャッシュの本文を短く要約する。キャッシュに無い事実は足さない。

優先度や、タスク化すべきだという推奨は書かない。

#### 3b. キャッシュに無いタスク（補足）

`M` 番号の扱いは従来どおり。キャッシュに無い理由は推測しない。完了・却下・担当外れなどの可能性だけを短く述べてよい。

次の3択をユーザーに聞く。Inbox 実行時点では status を変えない。

- 完了した → 反映するなら `done`
- 却下された → 反映するなら `canceled`
- 知らない → 変更不要。次回の照合でも再掲する

### 4. Wait

新規候補について、ユーザーが番号と project を明示するまで、task-manager を呼ばない。番号だけで project が無いときは、project を聞いて止まる。

`missing_from_cache` について、ユーザーが `M` 番号と `done` または `canceled` を明示するまで、task-manager で status を変えない。「却下で」だけでは変えない。`M1 を canceled にして` のように番号と status をセットで指示されたときだけ task-manager に渡す。

タイトルを変える指定が無いときは、キャッシュの title を使う。priority、start、end、estimate の指定が無いときは空欄として渡す。

### 5. Materialize

#### 5a. 新規タスク化

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

#### 5b. キャッシュ欠落タスクの status 更新

ユーザーが `M` 番号と `done` または `canceled` を明示したタスクだけを task-manager に渡す。渡す内容はタスク path と新しい status のみでよい。外部 Issue / 課題の close は行わない。
