---
name: execute-and-ship
description: レビュー済み計画を実行し、明示的な出荷認可を得た場合に、マージせずMR対応可能なCIまで継続する。
---

# 実行して出荷

レビュー済み計画またはレビュー済み短縮経路タスクで、ユーザーがこの複合スキルを明示的に選択した場合のみ使用する。ディスパッチ前に
`shipping_authorized: true` を記録する。これは限定されたコミット、プッシュ、MR、対象範囲内のCIループに対する包括的な権限であり、他の外部操作には及ばない。

この複合スキルが行うのは次のみである。

```text
execute-plan -> ship-change
```

最初に `execute-plan` を、adaptive implementation routing、canonical risk matrixによる単一snapshot review、ローカル検証の各ゲート付きで実行する。実行中はコミットしない。一致する
`LOCAL_COMPLETE`、または共有 evidence contract の D1 条件を満たす `LOCAL_VERIFICATION` を受け取ったら、共有 `~/.agents/workflows/software_delivery/references/review-common.md` のrisk分類（v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundary、v1 legacyは従来承認）と `human_review.py --context PATH` の検査に従い、`ship-change` に引き継ぐ。各phaseは最初の未完了ゲートから再開し、完了済みの外部書き込みを重複させない。

このスキルには`discovery`や`planning`を含めず、マージ、マージ後のクリーンアップ、リリース、タグ、本番環境、認証情報、権限変更、スコープ拡大を決して許可しない。
`context.json` を検証し、認可の欠落、snapshotの変更、protected-contract判断、外部CI/runnerの失敗、または証拠の不一致で停止する。次の
[task-execution.md](../../workflows/software_delivery/references/task-execution.md),
[review-snapshot.md](../../workflows/software_delivery/references/review-snapshot.md),
および [state-recovery.md](../../workflows/software_delivery/references/state-recovery.md) の契約を、ディスパッチ前に読む。
証拠の registry、receipt、CI 委譲の詳細は共有の `~/.agents/workflows/software_delivery/references/evidence-contract.md` を正本とする。
