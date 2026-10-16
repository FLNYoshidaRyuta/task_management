---
task_id: 40
title: '[技術負債] テストの node types 回避ハッチ（declare __dirname + @ts-expect-error）を一括解消する'
project: 開発標準化
start: ''
end: ''
estimate: null
priority:
- Low
status:
- todo
depends_on: []
github_type:
- github_issue
github_repo: mypl_pro
github_id: Issue#677
github_url: https://github.com/FutureLinkNetwork/mypl_pro/issues/677
github_updated_at: 2026-09-16 15:51:18+00:00
backlog_id: ''
backlog_url: ''
backlog_updated_at: ''
---
## 概要

`resources/js/Pages/Myplkun/__tests__/` ほか10ファイル以上のテストが、SCSS / ソースファイルを読むために次のハッチを慣行として使っている:

```ts
declare const __dirname: string;
// @ts-expect-error node types are not included in the app tsconfig.
import { readFileSync } from 'node:fs';
// @ts-expect-error node types are not included in the app tsconfig.
import { resolve } from 'node:path';
```

これは app tsconfig に `@types/node` が入っていないための回避で、現状は動作するが、**`@types/node` が `types` に入った瞬間、全ファイルの `@ts-expect-error` が "unused directive" となり tsc が一斉に落ちる**時限爆弾になっている（mypl_pro#670 のレーンで opus クロスレビューが指摘・検証済み）。

## やったこと

- (a) `@types/node` を導入し、全ファイルの `declare const __dirname` + `@ts-expect-error` を一括除去する
- (b) `vitest.config.ts` の `test.css` に `{ include: [/\?raw/] }` 相当を設定したうえで、`?raw` import へ一括統一する
- 対象ハッチが全テストファイルから消える
- コンテナ内 `npx tsc --noEmit` / `npx vitest run` / `npx prettier --check` が PASS
- SCSS 契約テスト（文字列マッチ系）が非空入力で機能していることの確認（`expect(...).not.toBe('')` ガードの維持）

## 残りのやること

- (a) `@types/node` を導入し、全ファイルの `declare const __dirname` + `@ts-expect-error` を一括除去する
- (b) `vitest.config.ts` の `test.css` に `{ include: [/\?raw/] }` 相当を設定したうえで、`?raw` import へ一括統一する
- 対象ハッチが全テストファイルから消える
- コンテナ内 `npx tsc --noEmit` / `npx vitest run` / `npx prettier --check` が PASS
- SCSS 契約テスト（文字列マッチ系）が非空入力で機能していることの確認（`expect(...).not.toBe('')` ガードの維持）
