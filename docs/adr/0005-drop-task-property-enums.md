# ADR 0005: Task property enums プラグインを廃止する

- Status: Accepted
- Date: 2026-10-09

## Context

`status` と `priority` をリスト型のまま扱い、Bases 一覧で固定候補から選ばせるため、Vault 同梱の Task property enums プラグインが Bases セルへ `<select>` を重ねていた。

この方式では、選択後の保存と Bases の再描画が競合し、一覧で変更した値がすぐ元に戻り、frontmatter にも残らないことがあった。

## Decision

Task property enums プラグインを廃止する。一覧とプロパティ欄の編集は Obsidian 標準のリスト編集に任せる。

`status`、`priority`、`source_type`、`github_type` は引き続き空リストまたは1件のリストとする。候補外の値や2件以上は `tasks/_scripts/validate_task_properties.py` と CI が検出する。取り得る値の一覧は `tasks/_config/property-choices.json` に置き、スクリプトと揃える。

## Consequences

一覧に固定の候補ドロップダウンは出ない。候補外や複数値は入力できるが、検証で検出する。

プラグイン用の Vault 設定と `.obsidian/plugins/task-property-enums/` はリポジトリから外す。`.obsidian/types.json` のリスト型定義と既存タスク frontmatter の形は変えない。
