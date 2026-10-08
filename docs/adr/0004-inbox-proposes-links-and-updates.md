# ADR 0004: Inbox は一致と更新差分を提案し、採用分だけ task-manager が書く

- Status: Accepted
- Date: 2026-10-08

## Context

Inbox は取得キャッシュと個人タスクを照合し、未タスク化候補と更新ありを提示する。
ユーザーが新規を選んでも、別ソースの同一作業や既存タスクとの関係は手順に含まれていなかった。
更新ありも、キャッシュが新しいことだけが分かり、タスクへ何を反映するかは手順に無かった。

一方、別ソースを自動で1タスクにまとめると、正本の `source_type` / `source_id` の意味が壊れる。
関係の種類（親子、`related`、`depends_on`）は作業の切り方に依存し、機械だけでは決められない。

## Decision

Inbox の手順に、ユーザー確認のあと次を挟む。

1. `tasks/_scripts/inbox_hints.py` で、ユーザーが選んだ新規・更新について一致と更新差分を Markdown で出す。
2. エージェントはその出力を根拠に、親子・`related`・`depends_on` と更新反映を提案し、採否をユーザーに確認する。
3. `task-manager` は、ユーザーが採用した作成・関係・更新だけを書く。

一致検出は決定論的に行う。

- `same_title`: タイトルの空白とコロン全角半角を揃えた一致
- `github_ref`: キャッシュ本文中の GitHub URL または `owner/repo#番号` と、選んだ新規または既存タスクの `source_id` の一致

比較は「選んだ新規同士」と「選んだ新規と既存タスク」に限る。既存タスク同士は比較しない。

`inbox_hints.py` は関係の種類を出力しない。別ソースを自動マージしない。
Backlog の status、priority、dueDate、estimatedHours を個人タスクの属性へコピーする提案もしない。

## Consequences

Inbox 実行中も、提案の採用前は `tasks/items/**` と `tasks/_タスク.md` は変わらない。
ユーザーは関係と更新を明示的に選べる。
照合の正本は引き続き `compare_inbox.py`、一致と更新差分の機械出力は `inbox_hints.py` に分かれる。
