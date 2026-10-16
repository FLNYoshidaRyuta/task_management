# ADR 0009: Google Chat はオンデマンドで読み、キャッシュしない

- Status: Accepted
- Date: 2026-10-16

## Context

GitHub と Backlog は `sources/` に取得キャッシュを置き、Inbox で個人タスクと照合する。Google Chat の会話は、依頼のたびに URL で指し示されることが多く、定期取得で一覧化する必要性が低い。メッセージ本文をリポジトリ外のキャッシュに残す運用も、ユーザー判断で採用しない。

[TASK_MANAGEMENT_PRINCIPLES.md](../TASK_MANAGEMENT_PRINCIPLES.md) の原則 9 は、外部情報の取得結果を `sources/` に置くことを定めている。

## Decision

- Google Chat は自動取得しない。`fetch_*` や Inbox の `--sources` に含めない。
- メッセージ本文は `sources/` に書かない。`sources/google-chat/` は作らない。
- 個人タスクの frontmatter に `google_chat_*` のチャンネルポインタは足さない。
- ユーザーが渡したメッセージ URL に対し、`tasks/_scripts/read_google_chat.py` が Google Chat API から読み、標準出力へ JSON を出す。
- 読む範囲は、指定メッセージ、同一スレッドの全件（上限 500 件、超過時は `truncated`）、スペース上の直前 1 件と直後 1 件。直前直後はスレッド内外を区別して示す。
- 認証トークンだけ `.google-chat-token.json` に保存する。これは資格情報であり、取得キャッシュではない。
- タスクへの反映は、ユーザーが新規または更新を明示したあと、`task-manager` だけが行う。採用された本文とメッセージ URL は、既存の「概要」「やったこと」「残りのやること」へ書く。

## Consequences

- 原則 9 の例外が 1 件増える。例外は本 ADR と原則本文に明記する。
- Inbox、`compare_inbox.py`、`skip_inbox.py`、`inbox_hints.py` は変えない。
- Google Cloud で Chat API と OAuth デスクトップクライアントの準備、`.env` の `GOOGLE_CHAT_CLIENT_ID` と `GOOGLE_CHAT_CLIENT_SECRET` はユーザーが行う。
- 対話手順は `.cursor/skills/google-chat-read/SKILL.md` が持つ。
