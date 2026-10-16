---
task_id: 93
title: グループニュース編集でイベントカレンダー解除待ちを画面に渡す
project: まいぷれバグ対応
status:
- canceled
start: ''
end: ''
focus_date: ''
priority: []
estimate: null
depends_on: []
related: []
github_type:
- github_pr
github_repo: mypl_pro
github_id: PR#1406
github_url: https://github.com/FutureLinkNetwork/mypl_pro/pull/1406
github_updated_at: 2026-10-15 12:56:44+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

Closes #1286。GroupNewsController::edit から eventUnlinkPending を Inertia に渡し編集画面の解除待ち UI を有効化。

## やったこと

- `GroupNewsController::edit` から Inertia prop `eventUnlinkPending` を渡す（店舗 `NewsController::edit` と同条件）
- `GroupNews/Edit.tsx` で `state.env.eventUnlinkPending` を設定し、既存の詳細設定シート（`AdvancedSettingsSheet`）の解除待ち UI を有効化
- `GroupNewsEditCopySeedTest` / `GroupNews/Edit.test.tsx` に回帰テストを追加
- 正常系
- 異常系
- 親 Issue: #1283
- 依存 PR（スタック）: #1405（`cursor/group-news-editor-commit-dates-70a0`）。**#1405 を main にマージ後**、本 PR をマージする
- 店舗側の同等実装: issue #350

## 残りのやること

- `GroupNewsController::edit` から Inertia prop `eventUnlinkPending` を渡す（店舗 `NewsController::edit` と同条件）
- `GroupNews/Edit.tsx` で `state.env.eventUnlinkPending` を設定し、既存の詳細設定シート（`AdvancedSettingsSheet`）の解除待ち UI を有効化
- `GroupNewsEditCopySeedTest` / `GroupNews/Edit.test.tsx` に回帰テストを追加
- 正常系
- 異常系
- 親 Issue: #1283
- 依存 PR（スタック）: #1405（`cursor/group-news-editor-commit-dates-70a0`）。**#1405 を main にマージ後**、本 PR をマージする
- 店舗側の同等実装: issue #350
