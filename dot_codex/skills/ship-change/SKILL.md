---
name: ship-change
description: 明示的に認可されローカルで完了した変更を、1回のコミット、プッシュ、MR、対象範囲内CIまで出荷し、マージまたはリリース前に停止する。
---

# 変更の出荷

明示的な `ship-change` 選択後、または出荷認可を記録した `execute-and-ship` の引き継ぎ後のみ使用する。入力は最終レビューとローカル検証を通過した
`LOCAL_COMPLETE`、または共有 evidence contract の D1 条件を満たす `LOCAL_VERIFICATION`。通常の実装は出荷を認可しない。

## 開始時と再開時のゲート

- 開始時または再開時に、`context.json`、固定されたdefault branch/base、artifact revision、allowlist、review/verification evidence、`review_snapshot_id`、記録済みのすべてのコミット、remote、MR、CI statusを検証する。欠落、古い、矛盾した、またはsnapshot不一致の証拠があれば停止する。
- ステージまたはコミット前に、`controller` はリポジトリの状態、意図したbase/head、allowlist、staged treeを調べ、secret、ローカルpath、内部workflow artifactがないか確認する。scannerを新たに作らず、汚染の疑いまたは利用できない証拠があればfail closedし、external dirtyまたはstaged pathを拒否する。
- ステージの直前にTask 4の `review_snapshot.py` identityとpreflightを再計算する。ステージ後はindexに対して再計算し、介在する変更なしにコミット直前にもindexに対して再計算する。external dirtyまたはstaged pathを拒否する。allowlistだけをstageし、レビュー済み・検証済み・stagedのidentityが完全一致することを要求する。不一致ならレビューと検証を無効にして停止する。

## controllerの出荷手順

Controller は共有 `~/.agents/workflows/software_delivery/references/review-common.md` のrisk gateを `human_review.py --context PATH` で再検査する。v2 LOWは人間待ちなし、MEDIUM/HIGHは現在提示の明示承認、v1 legacyは従来承認とする。commit 前に `check-gates --to COMMIT`、CI 収集に `evidence-ci`、完了前に `check-gates --to MR_READY` を実行する。コマンドと D1 の判定は共有の `~/.agents/workflows/software_delivery/references/evidence-contract.md` に従う。

`controller` は一致ゲート後に1回だけ論理コミットを作成し、記録済みブランチをプッシュして、固定されたWorktrunk default branchをターゲットとするMRを開く。再開時は検証済みのコミット、remote、MR証拠を再利用し、プッシュやMR作成を重複させない。CIを監視し、対象範囲内の実装修正だけを同じレビュー/検証/snapshotゲートに通してから再プッシュする。CI/runner失敗など外部ブロッカーには推測せずエスカレーションを使う。

このskillはMR_READYで停止し、マージ（`no merge`）、リリース、タグ付け、本番変更、認証情報または権限変更を決して行わない。mergeは後続の明示依頼時だけ `workflow_merge.py --context PATH --mr IID --sha FULL_SHA --authorize MERGE` を使う。未認可の出荷、snapshot/コミット/remote/MR/CI証拠の不一致、`external dirty state`、スコープ拡大、protected contractの判断、または外部失敗で停止する。

実行前に [task-execution.md](../../workflows/software_delivery/references/task-execution.md)、
[review-snapshot.md](../../workflows/software_delivery/references/review-snapshot.md),
[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md),
および `~/.codex/review-policy.md` を読む。ready MRがこのphaseのterminal resultであり、後のマージ後に限って `post-merge-cleanup` を明示的に提案する。
