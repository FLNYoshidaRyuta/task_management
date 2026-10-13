# ADR 0008: タスク化しない Inbox 候補を記録し再提案しない

- Status: Accepted
- Date: 2026-10-13

## Context

Inbox は取得キャッシュの未紐づけ項目を、毎回新規候補または追記候補として出す。ユーザーがタスク化しないと判断しても、その判断は会話に残るだけで、次回の照合で同じ項目が再度提案される。

個人タスクにしない判断も、運用上の判断として残したい。外部の更新があっても、明示的に戻すまで同じ候補を繰り返し出したくない。

## Decision

- タスク化しない判断は個人タスクにしない。`tasks/items/**` は作らない。
- 正本は `tasks/_config/inbox-skipped.json`。キーはキャッシュと同じ `source_type` と `source_id`。
- 書くのは `tasks/_scripts/skip_inbox.py` だけ。`--add` はキャッシュに存在する項目だけ受け付ける。
- `compare_inbox.py` は記録を読み、未紐づけかつ記録にある項目に `skipped` を付ける。Markdown の新規候補と追記候補から外す。更新ありとキャッシュに無い未完了タスクは従来どおり。
- 個人タスクへ同じキーが紐づいている項目は、記録よりタスクを優先する。更新ありの提案は出す。記録の自動削除はしない。
- 再提案するのは、ユーザーが `skip_inbox.py --remove` で記録を外したときだけ。外部更新では記録を戻さない。

Inbox 手順では、ユーザーが新規または追記の番号についてタスク化しないと明示したときだけ `--add` する。

## Consequences

- タスク化しない判断が Git で追える。Inbox の提示件数は減る。
- `compare_inbox.py` は記録を読むだけ。`task-manager` と `inbox_hints.py` は変えない。
- [docs/adr/0004-inbox-proposes-links-and-updates.md](0004-inbox-proposes-links-and-updates.md) の提案フローは維持する。除外は一覧提示の段階だけ。
