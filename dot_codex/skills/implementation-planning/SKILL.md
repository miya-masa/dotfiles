---
name: implementation-planning
description: 承認済みspecを追加判断なく実行できる、レビュー済みのvertical slice実装計画へ変換する。仕様承認後の複数ファイル変更、設計境界、依存順、検証手順の計画に使い、未確定のプロダクト判断や実装そのものには使わない。
---

# 実装計画

承認済みspecと証拠だけを入力に、実装担当が追加判断なく実行できる最小のplanを作る。詳細な契約は[spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md)に置く。

## ゲートとディスパッチ

- `context.json`、`spec.md`、レビュー結果を検証し、scope内の未決事項、normative gap、未記録の明示spec承認があれば計画しない。
- 通常の計画作成はfreshな上位モデルの`planning`へ渡し、下位workerが追加のproduct/architecture判断なく実行できるAC・interface・依存順・validationを揃える。既存決定の機械的な転記だけならControllerが直接計画する。重要な実装案が複数、境界をまたぐ、migration/rollout/rollback、認証認可、複雑な並行/分散状態ならmandatory。failureはstopまたはnarrow redispatchする。
- Goal、acceptance criteria、owned paths、一次証拠、protected constraints、検証command、stop条件を含むbounded packetを渡す。各active `D<n>`/`AC<n>`を理由とともに保持し、ACごとにexact test target/node ID・command・evidence pathを紐付ける。short path taskや未承認specを入力にしない。
- planは独立検証可能なvertical sliceへ分解し、各taskにgoal、owned paths、成果物、依存、入出力interface、AC、検証command、期待するRED理由、stop条件を持たせる。task内部はgoal・制約・完了条件を示し、手順は依存や失敗しやすい操作に限る。本番コード全文や共通TDD手順を貼らない。
- 詳細なID割当、tombstone、task/evidence mapping、checkpoint、final AC gateは共有referenceを正とし、ここでは重複して再定義しない。

## レビューと停止

Controller は plan 確定後、final review 前に `evidence.json` の registry・固定 check・実 hash を登録する。重要ACは既存spec/short taskのoracleを実装前に固定し、TASKS入口で対応checkとoracleをhash freezeする。risk triggerごとの検証選定は共有 `review-common.md` のriskに応じた検証を参照する。schema は `~/.agents/workflows/software_delivery/references/evidence-contract.md` に従い、ここで重複定義しない。

- 完成planへ`~/.codex/review-policy.md`のcanonical risk matrixを適用する。Controller検査は常に行い、matrixが要求するfresh reviewerへ**Spec compliance**と**Feasibility**（必要ならSimplicity）を最大2 lensで割り当てる。同一scopeの重複reviewは起動しない。findingは採用/却下/ユーザー判断と理由を記録する。
- reviewerがnormativeなspec gapを見つけたらplanで補わず`product-discovery`へ戻る。protected contract、architecture、権限、永続化、分散状態の未決は停止する。
- review通過後は「既存の実行依頼」に従う。実行依頼がなければ計画を報告して停止する。実行したいが終端が未選択の場合だけ `execute-plan` / `execute-and-ship` の二択と追加されるshipping authorityを説明する。

reviewの判定は`~/.codex/review-policy.md`に従う。

### 既存の実行依頼

`spec-and-plan.md` の同名節を正本とする。明示済みの実装依頼を phase 名で聞き直さず、選択を記録して続ける。plan のみの依頼では停止し、shipping は明示依頼なしに認可しない。
