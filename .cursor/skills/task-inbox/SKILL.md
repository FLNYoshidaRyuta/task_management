---
name: task-inbox
description: >-
  GitHub と Backlog の取得キャッシュを個人タスクと照合し、タスク化候補と更新を提示する。
  確認後は inbox_hints で一致・更新差分を出し、関係と反映内容を提案する。
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

照合は各タスクの `source_type` と `source_id` だけを使う。別ソースを同一タスクへ自動マージしない。

Inbox はタスクファイルを書かない。一致と更新差分は `inbox_hints.py` で機械的に出し、親子・関連・依存の種類と反映内容はエージェントが提案する。採用後だけ `task-manager` が書く。

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

ユーザーが新規候補も更新（`U`）も `M` の status 変更も選ばなかったときは、ここで終わる。

### 5. Propose

ユーザーが選んだ新規候補と更新（`U`）を、`source_type:source_id` に変換してから次を実行する。Markdown の番号の再解釈はスクリプトに渡さない。

```powershell
py .\tasks\_scripts\inbox_hints.py --sources github,backlog `
  --new backlog_issue:MYPL-4238 `
  --update backlog_issue:MYPL-4221
```

新規だけのときは `--new` だけ。更新だけのときは `--update` だけ。

出力の `## 一致` と `## 更新差分` を根拠に、ユーザーへ提案して止まる。スクリプト出力に無い関係や更新は提案しない。

#### 5a. 一致からの関係提案

`same_title` または `github_ref` があるときだけ、根拠ごとに次のいずれかを1つ提案する。

- 別ソースの同一作業 → `related`（1タスクにまとめない）
- 本文が親 Issue や移行対象を指している → `tasks/_タスク.md` の親子ネスト
- 作業順が本文に書いてある → `depends_on`

一致が無いときは関係提案を出さない。

#### 5b. 更新差分からの反映提案

`## 更新差分` があるとき、次を分けて提案する。

- `source_updated_at` をキャッシュに合わせる
- キャッシュ本文にありタスク本文に無い事実があれば、引用つきで本文追記を提案する
- 外部 state は参考として示す。個人タスクの `status` を外部 state に合わせる提案は、ユーザーが status を明示したときだけ含める

Backlog の status、priority、dueDate、estimatedHours を個人タスクの属性へコピーする提案はしない。

採用・不採用をユーザーに確認してから次へ進む。

### 6. Materialize

#### 6a. 新規タスク化

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

#### 6b. 更新の反映

ユーザーが採用した更新だけを task-manager に渡す。`source_updated_at` の同期、本文追記、ユーザーが明示した status 変更など、採用された項目だけを含める。

#### 6c. 関係の反映

ユーザーが採用した親子・`related`・`depends_on` だけを task-manager に渡す。不採用の関係は書かない。

#### 6d. キャッシュ欠落タスクの status 更新

ユーザーが `M` 番号と `done` または `canceled` を明示したタスクだけを task-manager に渡す。渡す内容はタスク path と新しい status のみでよい。外部 Issue / 課題の close は行わない。
