---
task_id: 37
title: '[技術負債] まいぷれくん agent-poc リファクタ epic（Phase 1-5）'
project: agent-poc
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
related:
- '[[tasks/items/開発標準化/docs： まいぷれくんリファクタ引き継ぎパック（Phase 3 以降）|docs： まいぷれくんリファクタ引き継ぎパック（Phase
  3 以降）]]'
- '[[tasks/items/agent-poc/test(agent-poc)： test_partner_api.py を実態に合う名前へ改名する|test(agent-poc)：
  test_partner_api.py を実態に合う名前へ改名する]]'
github_type:
- github_issue
github_repo: agent-dev
github_id: Issue#430
github_url: https://github.com/FutureLinkNetwork/agent-dev/issues/430
github_updated_at: 2026-09-16 15:24:29+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

agent-poc（実装 49,476行 / テスト 95,903行）から、振る舞い・契約・DB スキーマを変えずに読みにくさの原因を取り除く。誰も呼んでいないコードを消す、同じことを2箇所に書くのをやめる、巨大ファイルをほぐす。この3つだけを行う。

## やったこと

- 公開契約（chat-stream.v2 / SSE イベント形）の変更
- 新機能
- 本番で enforce か log_only か未確定の `src/security/` への変更（計画 §5）
- この変更は本体pro と OEM（business-console-pro）の両方へ波及する
- 各 PR は develop 向き。各 PR には対になる task issue を起票し、この issue の sub-issue として紐づける

## 残りのやること

- 公開契約（chat-stream.v2 / SSE イベント形）の変更
- 新機能
- 本番で enforce か log_only か未確定の `src/security/` への変更（計画 §5）
- この変更は本体pro と OEM（business-console-pro）の両方へ波及する
- 各 PR は develop 向き。各 PR には対になる task issue を起票し、この issue の sub-issue として紐づける
