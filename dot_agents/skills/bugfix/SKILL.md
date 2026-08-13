---
name: bugfix
description: "不具合修正のワークフロー（調査→再現→修正→検証）を controller がオーケストレーションするための指揮書。バグ・不具合・障害の修正で使う。explorer で原因特定、implementer で再現テスト→修正、verifier で検証。「バグを直して」「不具合修正」「この障害を調査して直す」などで参照。"
---

# Bugfix ワークフロー

controller はオーケストレーションと判断に集中し、調査・修正・fresh review・検証を subagent に委譲する。role 名は論理名である。Claude Code では `explorer` / `implementer` / `reviewer` / `verifier` を起動し、Codex では `explorer`（Luna・read-only）/ `worker`（Terra・workspace-write）/ `reviewer` を使う。

## フェーズと担当

| フェーズ | 担当 | 使う skill | 成果 |
|---|---|---|---|
| 1. 調査 | explorer | 本 skill の調査規律 | root cause 仮説と根拠 |
| 2. 再現 | explorer / verifier | project test tools | 最小再現と failing evidence |
| 2.5 worktree | controller | `execute-plan` の worktree gate | 隔離 worktree |
| 3. 修正 | implementer | `execute-plan` の RED → GREEN 契約 + 言語 skill | 最小差分と green test |
| 4. fresh review | reviewer | `review-lenses.md` + 言語 / 専門 review skill | Critical / Important の指摘 |
| 5. 検証 | verifier | `execute-plan` の local verification 契約 | 実入口に近い evidence |
| 終端 | controller | 出荷するなら `ship-change`、merge 後は `post-merge-cleanup` | 固定形式の完了報告 |

## 調査

1. 症状、期待動作、再現条件、直近変更を整理する。
2. explorer に関連コード、呼び出し元、状態遷移、ログとテストを追わせる。
3. 対立仮説を作り、観測または実験で棄却する。症状ではなく root cause を特定する。
4. 次のいずれかなら、別コンテキストの fresh explorer または専門 reviewer に read-only 診断を委譲する。
   - コード上の予測と観測が矛盾する。
   - プロトコル、コーデック、ライブラリ内部などの専門知識が決め手になる。
   - 実機実験でしか対立仮説を判別できない。
   - 2 回の探索または同等の時間を使っても root cause が絞れない。
5. 追加診断には症状、仮説と棄却理由、関連パス、期待動作を渡す。返答は元の explorer / verifier が裏取りする。

調査のみの依頼はここで終了してよい。再現できず、検証可能な仮説も得られない場合は当て推量で変更せず、得られた evidence と不足情報を報告する。

### 診断 brief

修正へ渡す前と調査のみの依頼を締める時は、Symptom（Expected / Actual）/ Reproduction / Root cause / Evidence（`file:line`・ログ）/ Impact scope / Regression test 条件 / Fix constraints / Unknowns にまとめる。原因未確定でも確度と不足証拠を書いてこの形で出す。

**診断レンズ**（controller が1パス、下記に該当すれば fresh reviewer へ委譲）: root cause が再現と evidence を過不足なく説明するか（相関を因果と取り違えていないか）/ 対立仮説を証拠で棄却できているか / Impact scope の限定が適切か / 証拠の穴を防御的な guard で埋めていないか。定義は `~/.agents/workflows/software_delivery/references/review-lenses.md` にある。

protected contract・データ損失・不可逆処理が絡む、または仮説が競合したまま残る場合は fresh reviewer に反証役として委譲する（`~/.agents/workflows/software_delivery/references/review-common.md` の共通制約に従う）。

## 修正

- worktree の要否は `execute-plan` の worktree gate に従う。
- failing reproduction test を先に確認し、最小修正で green にする。
- protected contract（CLAUDE.md 4原則1）へ波及するなら止まり、変更前にユーザー判断を得る。
- ガード条件追加で済む場合は既存ロジックを大きく変えない。

## Review と検証

- 実装文脈を持たない fresh reviewer が仕様適合、回帰、失敗時挙動、修正の単純さを確認する（レンズは `~/.agents/workflows/software_delivery/references/review-lenses.md` の実装後レンズ、起動 model は runtime 側の体制表に従う。self-review は代替にならない）。
- reviewer に severity の足切りを課さず、`~/.agents/workflows/software_delivery/references/review-common.md` の Finding gate と採用判定の二段構えで絞る。
- verifier が再現手順、focused test、必要な統合テストを実行し、修正前に失敗した入口が修正後に成功する evidence を示す。同じ evidence を取り直す重複検証は積まない。
- controller は diff と実行結果を裏取りし、変更内容 / 検証（失敗履歴含む）/ 残リスク / 人間が判断すべき点を報告する。
- **出荷まで進める場合**: `ship-change` の entry gate は workflow artifact（`context.json` / `LOCAL_COMPLETE` / `review_snapshot_id`）を要求するが、bugfix はそれを作らない。出荷する見込みが立った時点で `product-discovery` の short path に載せ（`tasks/01-short-path.md` + artifact init）、`execute-plan` の gate を通してから `ship-change` へ渡す。artifact を作らずに commit / push / MR を行わない。
