---
name: google-chat-read
description: >-
  ユーザーが渡した Google Chat メッセージ URL から会話を読み、内容を提示する。
  タスク化または既存タスクの更新は、ユーザーが明示したあと task-manager だけが行う。
  Google Chat、メッセージ URL、会話の取り込みを頼まれたときに使う。
  Inbox や定期取得には使わない。タスクファイルは変更しない。
---

# Google Chat Read

## Purpose

Google Chat の指定メッセージと、そのスレッド、スペース上の直前・直後を読み、ユーザーがタスクへ反映する内容を選べる状態にする。

## Rules

Inbox スキル（`task-inbox` / `task-inbox-unattended`）は使わない。`fetch_github.py` と `fetch_backlog.py` は呼ばない。

`tasks/items/**` と `tasks/_タスク.md` は変更しない。変更してよいのは task-manager だけ。

`sources/**` は作らず、編集しない。読んだメッセージ本文をファイルに残さない。

`.env` の内容は表示・要約・編集しない。トークンやクライアントシークレットを標準出力に出さない。

個人タスクの frontmatter に `google_chat_*` は足さない。採用した本文とメッセージ URL は、task-manager が既存の「概要」「やったこと」「残りのやること」へ書く。

優先度、期限、見積もり、完了、タスク化の推奨は書かない。キャッシュに無い事実は足さない。

## Procedure

PowerShell では `py -3`、bash では `python3` を使う。

### 1. Read

ユーザーがメッセージ URL を渡す。次を実行する。

```powershell
py -3 tasks/_scripts/read_google_chat.py --url "https://chat.google.com/room/SPACE/THREAD/MESSAGE"
```

```bash
python3 tasks/_scripts/read_google_chat.py --url "https://chat.google.com/room/SPACE/THREAD/MESSAGE"
```

リソース名 `spaces/SPACE/messages/MESSAGE` も受け付ける。スペース URL やスレッド URL だけでは読めない。

失敗したときは stderr の文言をそのままユーザーに伝え、終了する。

### 2. Present

標準出力の JSON を読み、次を提示する。

- **スペース**: `space.displayName` と `space.spaceType`
- **指定メッセージ**: `target`
- **スレッド**: `thread` を `createTime` 昇順のまま。`truncated` が true のときは上限超過を短く述べる
- **直前**: `before`（`inThread` でスレッド内外を示す）
- **直後**: `after`（同様）

添付は名前だけ。中身は取得しない。

### 3. Wait

ユーザーが次のどちらかを明示するまで、task-manager を呼ばない。

- **新規**: project を明示する。無いときは project を聞いて止まる。title の指定が無いときは、指定メッセージの先頭を短く切った題名を提案し、確認する
- **更新**: `task_id` またはタスクファイルと、書き換える見出し（「概要」「やったこと」「残りのやること」のいずれか）を明示する

### 4. Hand off to task-manager

渡す内容は、ユーザーが採用した文章とメッセージ URL だけとする。`priority`、`start`、`end`、`estimate`、`github_*`、`backlog_*` は指定が無ければ空のまま渡す。

新規のときは project、title、採用本文、URL を渡す。更新のときはタスクの特定、見出し、採用本文、URL を渡す。
