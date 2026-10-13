---
name: commit-push
description: 作業ツリーの差分を commit し、現在のブランチを push する。
---

## 手順

1. `commit-push` サブエージェントを Task で起動する。モデルはサブエージェント定義の `model` に従う。
2. 差分の読み取り、コミット範囲とメッセージの決定、commit、push はすべてサブエージェントに任せる。親エージェントでは git の add / commit / push を行わない。
3. サブエージェントの完了報告を、そのままユーザーへ返す。
