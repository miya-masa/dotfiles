---
name: product-discovery
description: 曖昧な機能アイデアや要求を対話で実装可能な spec へ整え、fresh review を通してユーザー承認まで持っていく時に使う。「〜を作りたい」「〜できるようにしたい」「要件を整理して」「仕様を詰めたい」「ブレストしたい」などで起動。既に確定した spec の実装計画（implementation-planning）や、不具合の原因調査（bugfix）には使わない。
---

# Product Discovery

曖昧な要求を、実装可能で review 済みの spec に変える phase。controller は高影響な product 判断だけをユーザーと合意し、**コードや plan を変更しない**。

契約の詳細は [references/spec-and-plan.md](references/spec-and-plan.md)、起動体制と packet は [references/roles.md](references/roles.md) にある。

## 開始時

artifact 初期化の前に共通 `~/.agents/workflows/software_delivery/references/effort-policy.md` の直接完了条件を確認する。明確・局所・可逆で protected contract 非該当、かつ委譲コストが作業を上回る小さい実装依頼なら controller が直接完了し、この phase を開始しない。既存 workflow ID / active AC がある依頼、明示的な spec / plan 作成、durable resume、shipping、未決の要求・境界がある場合は以下の正式 workflow を使う。

`workflow_artifact.py init` で `.aidocs/workflows/<workflow-id>/` を作り、`context.json` を phase `DISCOVERY` で初期化する（CLI は `~/.claude/skills/execute-plan/references/state-and-artifacts.md`）。init に失敗したら workflow を始めない。以後 phase 遷移は `workflow_state.py transition --expected-revision N` だけで行い、報告や `progress.md` から進めない。

## 対話と探索

- Goal、利用者、Context、Constraints、scope、non-goal、主要方針、失敗条件を確認する。
- 結論を変える未決事項がある時だけ、現在の理解と不足情報を短く示す。根拠のない確度の数値は付けない。
- **repository から分かる事実（コード / test / docs / schema / public interface）をユーザーに尋ねない。** 広く探す必要がある調査は `explorer` に委譲し、読む先が分かっているファイルは controller が読む。
- 実質的な選択が残る時だけ方針を比較する。依存する質問は順番に、独立した判断は推奨案付きでまとめて聞く。回答ごとに evidence packet を更新し、事実 / 推論 / 仮定 / 未決の分離と Given/When/Then を検査する。
- 実質的な仕様検討は `deliberator`（`task_kind=specification`）へ渡す。Controllerが根拠・要求との一致を検査し `spec.md` へ統合する。既存決定の転記だけなら直接行う。

## spec review gate

draft が揃ったら共有 `~/.agents/workflows/software_delivery/references/review-common.md` のリスク基準を適用する。通常は fresh `reviewer` 1 体で、該当する Completeness / Soundness / Operability / Simplicity をまとめて確認する。protected contract 等は Adversarial も確認する。独立したリスク反証が必要な時だけ lens を分ける。finding は `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類し、採用分を反映して影響 scope だけ再 review する。normative な gap は spec 起こしへ戻す。

クロスモデル確認をユーザーが明示依頼した時だけ、`references/roles.md` の「herdr 内クロスモデル並走」に従う（execute-plan では `~/.claude/skills/product-discovery/references/roles.md`）。端末環境だけを理由に追加 reviewer を起動しない。

## 停止と handoff

discovery 担当は spec / short task に canonical AC table を1つ作り、Controller が source を確定する。形式と後続の registry 登録は `~/.agents/workflows/software_delivery/references/evidence-contract.md` を参照する。
重要ACは実装前に既存spec/short taskのoracleへ期待値・禁止例・不変条件を固定し、対応する既存checkを記録する。後続のTASKS入口でoracleとcheckをhash freezeする。

- **spec 相当 artifact を持つ workflow では**、外部サーフェス（`## 外部サーフェス` 節の内容またはゼロ件宣言）が `agreed` でなければ、`spec 承認の要求`・`実行方法の選択の提示`・次 phase への `handoff`・`session をまたぐ中断（compact を含む）` へ進まない。保留と意図しない中断からの再開は [references/spec-and-plan.md](references/spec-and-plan.md) の `## 外部サーフェス合意` が定める例外に従う。
- **review 反映済み spec をユーザーが明示承認するまで、実装に進まない。** 承認は `context.json` と `progress.md` に記録する。
- 承認を求める直前に、`reviews/` の Simplicity finding（**解法の代替 / エッジケース削減の両方**）の要点とcontroller の採否を **1 行**で提示する（どちらも無ければ「指摘なし」）。同じ 1 行を `progress.md` にも残す。short path と調査のみで停止する場合は課さない。代替案の finding は既定で `却下（根拠付き）` とし、それだけを理由に `要ユーザー判断` へ上げない（この 1 行が唯一の歯止め）。
- 通常経路では、次の phase として `implementation-planning` **だけ**を案内する。plan が無い段階で実行方法の選択を提示しない。
- ただし spec review に未解消 finding が無く、plan が spec の決定を task へ落とすだけになる（＝ `implementation-planning` の plan review skip 条件をすべて満たす）と判断できるなら、spec・plan・実行方法の二択を **1 回の提示にまとめてよい**。phase 遷移を確認するためだけの往復を作らない。この場合も spec 承認と実行方法の選択は個別に `context.json` へ記録し、記録するまで実装を始めない。
- 調査だけの依頼なら、spec と未決事項を出して停止する。
- short path の条件（要求・外部挙動・AC・validation が明確、実装時に残る設計判断が無い、protected contract / migration / architecture 判断 / 複雑な並行処理なし、既存の未コミット変更を安全に分離できる）を**すべて**満たす時だけ、`tasks/01-short-path.md` を作り、実行選択は `implementation-planning` の「既存の実行依頼」に従う（未選択時だけ二択と shipping 権限を説明する）。**ファイル数では判断せず、preflight review も挟まない**（差分全体は `execute-plan` の final review が見る）。short path でも実行選択の記録を省略しない。
- 既に spec 相当が確定している依頼（確定済みの Story など）は、discovery 対話を省いて spec review gate から始める。
- planning を案内する時、session 引き継ぎ（`handoff` skill、既定 compact）の要否を評価する。基準は `~/.claude/skills/product-discovery/references/session-handoff.md`。

## この phase が行わないこと

コード変更、plan 作成、実装、commit / push / MR、merge、cleanup。実装権限も shipping 権限もここでは発生しない。
