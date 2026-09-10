---
name: product-discovery
description: 曖昧な機能アイデアを対話で実装可能な仕様へ整える。ブレインストーミング、要件整理、インタビューしてほしい、仕様を詰めたい、解決策やUXが未確定という依頼で使う。明確な仕様の実装や不具合原因の調査には使わない。
---

# プロダクトディスカバリ

`controller` は影響の大きいプロダクト判断だけをユーザーと合意し、コードやplanを変更しない。

## 開始

artifact 初期化の前に共通 `~/.agents/workflows/software_delivery/references/effort-policy.md` の直接完了条件を確認する。明確・局所・可逆で protected contract 非該当、かつ委譲コストが作業を上回る小さい実装依頼なら controller が直接完了し、この phase を開始しない。既存 workflow ID / active AC がある依頼、明示的な spec / plan 作成、durable resume、shipping、未決の要求・境界がある場合は以下の正式 workflow を使う。

正式 workflow では [spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md) を参照する。[artifact-lifecycle.md](../../workflows/software_delivery/references/artifact-lifecycle.md) は作成・移設時、[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md) は再開・state 更新時に必要な節だけ読む。同一 session で既読の instruction を再読しない。
正式 workflow の新規リクエスト（通常または短縮）では、規範判断の前に必ず `new-id` → `init` → `workflow_state.py validate` を実行し、`DISCOVERY` revision `0` を確認する。

## 再開

新規リクエストでは `terminal artifact` を自動再開しない。再開対象は、ユーザーが明示した `explicit exact workflow ID/path` または現sessionが保持するIDだけとする。IDがなければ `nonterminal` だけを候補にし、`single unambiguous nonterminal` だけを選ぶ。複数候補があれば、ユーザーに1回だけ選択を求めて停止する。
`identity`、`schema`、`phase`、`revision`、`source root`、`committed evidence` を検証し、最初の `first incomplete committed gate` からだけ続ける。再開は停止済みのprior `controller` を前提にし、live `controller` が見つかれば拒否する。concurrent `controller` はunsupportedであり、multi-writer flowとして扱わない。

## 対話

- Goal、利用者、Context、Constraints、scope、non-goal、主要方針、失敗条件を確認する。事実はrepositoryを限定探索し、ユーザーへ尋ねない。
- 各work unitを`DIRECT / OPTIONAL_DELEGATION / MANDATORY_SPECIALIST`に分類し、根拠をartifactへ記録する。限定探索と既存決定の転記はControllerが行い、実質的な仕様検討はfreshな上位モデルの`specification`へ渡す。
- 広いread-heavy探索を独立したbounded workstreamへ分割でき、speed/coverage/focusを実質的に改善する場合だけfresh `explorer`を任意利用する。逐次依存またはshared mutable stateを並列化しない。
- 要求解釈が複数、既存挙動と矛盾、外部挙動/state/error/permission/boundaryが未定義、product判断またはprotected-contract判断が必要な場合はfresh 上位モデル / high `specification`をmandatoryとする。unavailable、根拠不足、矛盾、boundary wideningではstopまたはnarrow redispatchし、Controller直行へfallbackしない。
- ユーザーに問うのは、repository evidenceと合意済みの前提から一意に導けず、観測可能な結果・scope・protected contractを変え、かつproductの価値判断またはユーザーの優先順位が必要、という3条件をすべて満たすproduct decisionだけとする。既存挙動の継承、合意済みnon-goalの帰結、generator標準挙動、実装詳細は事実・導出制約・implementation noteとして記録し、open decisionにしない。
- 実質的な選択が残る時だけ方針を比較する。依存するproduct decisionは原則1問とし、独立したdecisionは推奨案を付けて最大3件まで一括確認できる。回答ごとにevidence packetを更新し、事実・仮定・未決・Given-When-Thenを検査する。
- draft後は`~/.codex/review-policy.md`のcanonical risk matrixを適用する。reviewer数やlensをphase名で固定せず、findingは採用・却下・ユーザー判断に分類して記録する。

## 短縮経路

- `short path` は明確な要求/AC/検証、局所的で設計判断が残らない変更、protected contract等なし、安全な変更分離という全条件に `affirmative evidence` がある場合だけ許可する。`validated artifact` とController検査を満たし、canonical risk matrixが要求する場合だけfresh reviewを行う。その後の実行選択は `implementation-planning` の「既存の実行依頼」に従い、未選択時だけ `execute-plan` / `execute-and-ship` の二択を提示する。`execute-and-ship` は `shipping authority` だけを追加し、`approved scope` を拡大しないと説明する。
- 短縮経路では、外部サーフェス節が揃っていることも許可条件に含めます。
- `Ambiguity`、`missing evidence`、疑い、`boundary/protected-contract impact`、または `Important finding` があれば `execution choice` を保留し、上位モデルの `specification` pathへ戻す。

## 停止

discovery 担当は spec / short task に canonical AC table を1つ作り、Controller が source を確定する。形式と後続の registry 登録は `~/.agents/workflows/software_delivery/references/evidence-contract.md` を参照する。

- 仕様相当artifactを持つ場合、[spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md)の`## 外部サーフェス合意`が定める外部サーフェスが`agreed`になるまで、spec 承認の要求・実行方法の選択の提示・次phaseへのhandoff・session をまたぐ中断（compact を含む）のいずれにも進まない。保留と意図しない中断からの再開は同節が定める例外に従う。
- review反映済みspecをユーザーが明示承認するまでplanningや実装へ進まない。確認前は引き継がない。normative gapや証拠不足は`specification`へ戻す。
- 承認直前に`reviews/`のSimplicity finding（解法の代替 / エッジケース削減の両方）の要点と採否を1行で提示し、同じ1行を`progress.md`にも残す（short pathと探索のみの停止では不要）。Simplicity findingなしは「指摘なし」を記録し、代替案findingは既定で`却下（根拠付き）`とし、それだけを理由に`ユーザー判断`へ上げない。
- 通常のreview済みspec完了時は次phaseとして`implementation-planning`だけを案内し、plan review前の実装/実行選択は提示しない。
- 重要ACは実装前に既存spec/short taskの`active[].oracle`へ期待値・禁止例・不変条件を固定し、対応する既存checkを記録する。後続のTASKS入口でこのoracleとcheckをhash freezeする（詳細は共有evidence contract）。
- 仕様briefはGoal/利用者、Constraints、Non-goals、normative requirements、flow/edge、compatibility、AC、assumptions、open decisionsを含める。探索だけならspecと未決で停止する。
- reviewの判定は`~/.codex/review-policy.md`に従う。
