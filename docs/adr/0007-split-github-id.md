# ADR 0007: GitHub ポインタを github_repo と表示用 github_id に分ける

- Status: Accepted
- Date: 2026-10-10

## Context

個人タスクの `github_id` に `owner/repo#番号` を1フィールドで持っていた。一覧ではリポジトリと番号を分けて見たい。種類は既に `github_type` がある。

取得キャッシュの `sourceId` と Inbox コマンドの `github_issue:owner/repo#番号` は運用が定着している。

## Decision

- 非ルーティーンの GitHub ポインタは次の5つで表す。
  - `github_type`（`github_issue` または `github_pr`）
  - `github_repo`（リポジトリ名のみ。owner は `github_url` に載せる）
  - `github_id`（`Issue#番号` または `PR#番号`）
  - `github_url`
  - `github_updated_at`
- 種類の正は `github_type`。`github_id` の接頭辞は表示形であり、不一致は検証で落とす。
- `sources/**` の `sourceId` と Inbox の照合キーは `owner/repo#番号` のまま。タスクでは `github_url` の owner と `github_repo`・番号を組み立てる。
- GitHub ポインタが無いタスクへ空の `github_repo` は足さない。

## Consequences

- ADR 0004 の「`github_id` が `owner/repo#番号`」という記述は本 ADR に置き換わる。0004 の本文は歴史として残す。
- `validate_task_properties.py` と `task_source_links.py` が新形式を正本とする。
- `tasks/タスクビュー.base` の一覧に `github_repo` 列を足す。
