---
name: bugfix
description: 既存の不具合を再現・局所化し、最小修正と必要十分な検証まで進める。「バグを直して」「障害を調査して直す」で使う。単純な修正は controller が直接完了し、原因未確定・証拠矛盾・設計判断が残る場合だけ診断を広げる。
---

# Bugfix

通常は controller が `symptom → reproduction/evidence → cause → minimal fix → targeted validation` を完了する。作業量・委譲・effort は共通 [effort-policy.md](../../workflows/software_delivery/references/effort-policy.md) に従う。

## 直接完了する条件

期待動作が既存 code/test/docs から明確で、原因を evidence が説明し、修正が局所的・可逆で protected contract や複雑な状態へ波及せず、委譲コストが作業を上回る小変更なら直接修正する。explorer / implementer / verifier、計画、workflow artifact、worktree 作成を前処理にしない。既存のユーザー変更を分離できない場合は先に変更場所を確保する。

不具合を示す failing test または再現 evidence を確認し、最小修正後に同じ入口を検証する。追加 test は回帰を検出できる場合に作る。再現不能でも原因を断定せず、不足証拠と次の判別手段を示す。調査だけの依頼ならコードを変更しない。

## 診断を広げる条件

再現できない、複数 subsystem に跨る、回帰の起点が原因判定に必要だが不明、architecture 判断が必要、targeted test が失敗、または証拠が矛盾する場合は、未解決の問いだけを調べる。環境・入力・推論の失敗を区別し、同じ探索を繰り返さない。

競合仮説が残る、証拠が理解を否定する、異なる修正が 2 回失敗した場合は fresh 診断を使う。Codex は `debugging`、Claude は `deliberator`（`task_kind=debugging`、model / effort は runtime の roles.md）へ渡す。protected contract・データ損失・不可逆処理の判断には該当専門家とユーザー合意を得る。専門診断に不足や矛盾があれば問いを絞って戻し、推測で修正しない。

委譲時は Expected / Actual、Reproduction、first divergence、Root cause と確度、Evidence（path:line / log）、棄却した仮説、Impact scope、Regression test 条件、Fix constraints、Unknowns を短く渡す。controller は結論を左右する一次証拠だけを裏取りする。新しい仕様判断が必要な時だけ `product-discovery` へ移り、診断を取り直さない。

## Review・検証・完了

review はリスクで決める。Codex は `~/.codex/review-policy.md`、Claude は共有 [review-common.md](../../workflows/software_delivery/references/review-common.md) を正本とし、軽微な修正は self-check、必要な場合だけ fresh reviewer を使う。必須の独立 review を self-review で代替しない。

controller が targeted validation と必要な統合検証を行い、[review-common.md](../../workflows/software_delivery/references/review-common.md) のrisk分類を適用する。v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。[evidence-contract.md](../../workflows/software_delivery/references/evidence-contract.md#人間レビューの記録と操作) のhelperで現在の検査を行った後、変更・原因・検証（失敗履歴を含む）・残る未確認範囲を報告する。実行済み evidence を verifier に取り直させない。 `HERDR_ENV=1` の時は報告の直前に `nvim-review-open --base <比較起点>` を 1 回実行し、同じ workspace の nvim に `base..作業ツリー` の diffview を開いてフォーカスを移す。**待ち方は risk 区分のまま**変えず、失敗したら 1 行報告して続ける。

出荷を依頼された場合、`ship-change` は `context.json` / `LOCAL_COMPLETE` / `review_snapshot_id` を要求する。既存 evidence を再利用して `product-discovery` の short path（条件外なら通常経路）で artifact を初期化し、`execute-plan` の gate を通す。承認や完了 state を捏造せず、artifact なしに commit / push / MR を行わない。shipping・merge・cleanup の権限は修正依頼から推論しない。

原因・修正条件が確定した通常規模の実装は下位 implementer / worker へ渡す。計画不足は上位の仕様・計画へ戻し、実装固有の推論が難しい時だけ共通 effort policy の上位実装経路を使う。
