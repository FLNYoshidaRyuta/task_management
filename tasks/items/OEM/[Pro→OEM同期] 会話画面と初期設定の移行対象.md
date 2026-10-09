---
task_id: 56
title: "[Pro→OEM同期] 会話画面と初期設定の移行対象"
project: OEM
status:
  - in_progress
start: ""
end: ""
priority:
  - Mid
estimate:
depends_on: []
related: []
github_type:
  - github_issue
github_id: FutureLinkNetwork/business-console-pro#667
github_url: https://github.com/FutureLinkNetwork/business-console-pro/issues/667
github_updated_at: 2026-10-09T13:00:20Z
backlog_id: ""
backlog_url: ""
backlog_updated_at: ""
---
## 概要

mypl_pro の変更を OEM（ビジネスコンソール）へ移行適用するための、移行対象項目の管理。

比較対象は次の develop。

- mypl_pro `8162874f`
- business-console-pro `ef79ca86`

画面のパスは同じで、実装は分岐している。

- 会話画面: 両方とも `GET /shop/{id}` → `Myplkun/Main`
- 初期設定: 両方とも `GET /onboard/{id}` → `Onboard/Show`
- 共通バックエンド: 両方とも agent-dev へ接続。識別子は `caller=mypl` / `caller=oem`

ビジネスコンソールにだけ残っている変更の判断は [mypl_pro#1367 のコメント](https://github.com/FutureLinkNetwork/mypl_pro/issues/1367#issuecomment-6032291777) に合わせて見直した。agent-dev の契約変更は、どの項目でも不要。

## やったこと

- 理解カードの2択、5〜10枚、自由記述への一本化は 2026-08-24 に同期済み
- ビジネスコンソールにだけ残っている変更の判断を mypl_pro Issue1367 のコメントに合わせて見直した
- agent-dev の契約変更は、どの項目でも不要と判断した

## 残りのやること

会話画面 `/shop/{id}` の適用候補:

1. 初期設定の前にウェブ情報学習
2. テーマ選択直後の再読込復元
3. 固定写真ゲート
4. 自由入力の失敗時に文章を戻す
5. 再開の第一声をおさらいにする
6. 再開時に前回写真を添える
7. 確定 revision をサーバー正本にする
8. mode-start を共通処理にする
9. やり直しで journey を初期化する
10. 開始案内の一つ前へ戻る
11. 月次上限と緊急停止を分ける
12. 独自媒体の失敗を対象別に出す
13. 独自媒体 ID の検証
14. 媒体別の生成中表示
15. 完了本文を途中差分より優先
16. 契約違反を観測へ送る
17. 生成媒体を capabilities で決める
18. 入場時にコピー専用セッションを捨てる

初期設定画面 `/onboard/{id}` の適用候補:

1. 確認画面の未保存離脱警告
2. 言い方の表示と保存を分ける
3. 初期設定を店舗単位にする
4. 手動確認が必要な選択は保存しない
5. 保存エラーを操作バー内に出す
6. 公開する項目を限定する
7. 既存店舗の基準日

移行時の注意（console の既存仕様を退行させない）:

- 会話中の画面離脱確認
- 投稿ドラフトの表示状態
- 初期設定 AI などの実行記録
