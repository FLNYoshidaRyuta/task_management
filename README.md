# task_management

タスク管理

## セットアップ

PowerShell では `py -3`、bash では `python3` を使う。

```powershell
py -3 -m pip install -r requirements.txt
```

```bash
python3 -m pip install -r requirements.txt
```

## Google Chat（オンデマンド）

GitHub / Backlog と別に、Google Chat のメッセージ URL を渡したときだけ会話を読む。`sources/` には残さない。

1. Google Cloud で [Google Chat API](https://developers.google.com/workspace/chat) を有効化する。
2. OAuth 同意画面を設定し、デスクトップアプリの OAuth クライアント ID を作成する。
3. `.env` に `GOOGLE_CHAT_CLIENT_ID` と `GOOGLE_CHAT_CLIENT_SECRET` を書く（`.env.example` を参照）。
4. 初回実行時にブラウザで同意する。トークンは `.google-chat-token.json` に保存される（git 管理外）。

```bash
python3 tasks/_scripts/read_google_chat.py --url "https://chat.google.com/room/SPACE/THREAD/MESSAGE"
```

対話でのタスク化・更新は `.cursor/skills/google-chat-read/SKILL.md` を使う。設計の根拠は [docs/adr/0009-google-chat-on-demand-read.md](docs/adr/0009-google-chat-on-demand-read.md)。

## テスト

```powershell
py -3 -m unittest discover -s tasks/_scripts -p "test_*.py"
```

```bash
python3 -m unittest discover -s tasks/_scripts -p "test_*.py"
```
