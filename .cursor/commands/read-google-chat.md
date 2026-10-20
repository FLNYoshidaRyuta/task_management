---
name: read-google-chat
description: Google Chat のメッセージ URL から会話を読み、タスク化または更新の準備をする。
---

## 手順

`.cursor/skills/google-chat-read/SKILL.md` に従う。

1. ユーザーに Google Chat のメッセージ URL（「リンクをコピー」）を求める。
2. `tasks/_scripts/read_google_chat.py --url "..."` を実行する。
3. 指定メッセージ、スレッド、直前、直後を提示する。
4. ユーザーが新規または更新を明示したあと、task-manager に採用内容だけを渡す。

Inbox の取得は行わない。`sources/` は使わない。
