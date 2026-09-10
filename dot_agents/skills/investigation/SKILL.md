---
name: investigation
description: コードを変えず「どう動く」「どこで処理する」「原因だけ知りたい」に repository の証拠で答える。読む先が明確なら直接調べ、独立した広い探索だけ委譲する。修正依頼や一般的な文書作成の前処理には使わない。
---

# Investigation（軽量調査）

コードを変えずに調べて答える。調査量と委譲は共通 [effort-policy.md](../../workflows/software_delivery/references/effort-policy.md) に従う。読む先が明確なら controller が直接読む。独立した広い探索にのみ `explorer` を使う。

- **read-only**。修正が必要と判明しても自動で変更せず、切替を提案して止まる。
- explorer の報告は鵜呑みにせず、結論を左右する code path だけ裏取りする。
- 結論・根拠（`path:line`）・未確認事項を要約する。観測と推測を混ぜない。

## 境界

| 求められていること | 進め方 |
|---|---|
| 調べて答えるだけ | investigation で完了 |
| 既存不具合の原因を直す | bugfix へ切替提案 |
| 仕様を追加・変更する | `product-discovery` へ切替提案（以降は機能開発ワークフロー） |

問いに答える一次証拠が揃えば終了する。未解決の原因は `bugfix` の診断規律を参照し、再現不能と原因未確定を区別する。`codebase-onboarding` は全体の onboarding guide が依頼された場合だけ使う。
