# ADR 0006: Inbox の更新対象は会話コメントを別キャッシュへ取る

- Status: Accepted
- Date: 2026-10-10

## Context

Inbox の一覧取得は、GitHub の `body` と Backlog の `description` だけをキャッシュする。更新日時はコメントが付いただけでも進むが、コメント本文は提案の根拠に入らない。

更新差分は説明欄を短く切っていたため、長い説明の後半も提案根拠から落ちる。

個人タスク本文は「概要」「やったこと」「残りのやること」の3節で書く。1タスクは GitHub と Backlog をそれぞれ0または1件持てる（ADR 0004 dual-source pointers）。

## Decision

- 通常の一覧取得ではコメントを取らない。
- ユーザーが更新（U）を選んだチャンネルだけ、`tasks/_scripts/fetch_comments.py` で会話コメントを取り、`sources/github/comments.json` と `sources/backlog/comments.json` に保存する。
- `inbox_hints.py` の更新差分には、選ばれたチャンネルの説明欄全文とコメント全文を出す。コメントキャッシュが無い id は `未取得`、0件は `0`。
- エージェントはその出力を根拠に、3節の本文を提案する。採用前は `tasks/items/**` を変えない。
- 片方のチャンネルを更新しても、既存本文にある他チャンネルの事実は消さない。同期するのは選ばれたチャンネルの `github_updated_at` または `backlog_updated_at` だけ。
- 一致検出（`same_title` / `github_ref`）は説明欄だけを見る。コメント本文から関係は提案しない。
- PR の行コメントとレビュー判定本文は対象外。会話スレッドだけを取る。

## Consequences

- コメント取得は更新対象の件数に比例する。一覧取得の API 回数は増えない。
- `sources/**/comments.json` は読み取り用キャッシュ。エージェントは手で編集しない。書くのは `fetch_comments.py` だけ。
- [docs/adr/0004-inbox-proposes-links-and-updates.md](0004-inbox-proposes-links-and-updates.md) の提案フローは維持し、更新差分の材料が増える。
