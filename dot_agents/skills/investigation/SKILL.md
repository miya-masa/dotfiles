---
name: investigation
description: コードを変えずに「どう動いてる」「どこで〜してる」を調べて答える軽量調査の指揮書。explorer agent を起動して読解・トレースし、結果を要約する。read-only（修正・実装はしない）。「調べて」「どう動いてる」「どこで〜してる」「アーキテクチャ把握」「原因だけ知りたい」などで使う。修正まで必要なら bugfix / 機能開発ワークフローに切り替える。
---

# Investigation（軽量調査）

コードを変えずに調べて答える。広く探す必要がある時だけ explorer role に委譲し、読む先が分かっていれば controller が直接読む。role 名は論理名である。Claude Code では `explorer` / `implementer` / `reviewer` / `verifier` を起動し、Codex では `explorer`（Luna・read-only）/ `worker`（Terra・workspace-write）/ `reviewer` を使う。

- **read-only**。修正が必要と判明しても自動で変更せず、切替を提案して止まる。
- explorer の報告は鵜呑みにせず、結論を左右する code path だけ裏取りする。
- 結論・根拠（`path:line`）・未確認事項を要約する。観測と推測を混ぜない。

## 境界

| 求められていること | 進め方 |
|---|---|
| 調べて答えるだけ | investigation で完了 |
| 既存不具合の原因を直す | bugfix へ切替提案 |
| 仕様を追加・変更する | `product-discovery` へ切替提案（以降は機能開発ワークフロー） |

原因の深掘りは `bugfix` の診断規律、codebase 全体の把握は `codebase-onboarding` を explorer に適用する。
