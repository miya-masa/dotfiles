---
name: execute-plan
description: 承認済み計画または短縮経路タスクと、context.jsonに記録済みの実装依頼がある時に、実装・risk-based review・ローカル検証まで進める。未承認の仕様、計画作成、出荷には使わない。
---

# 計画実行

レビュー済み計画または短縮経路タスクと、`context.json` に記録済みの execution choice を入力にする。phase 名の選択でも、planning が既存の明示的な実装依頼から記録した選択でもよい。記録前や未承認 spec からは実装しない。実行の詳細は [task-execution.md](../../workflows/software_delivery/references/task-execution.md) を参照する。

## 開始時とworktreeのゲート

- `context.json`、承認済みspec/planまたは短縮経路タスク、レビュー報告、タスク証拠、Git証拠を開始時とすべての再開時に検証する。欠落、古い、矛盾した、または状態より先行した証拠があれば、workerのディスパッチ前に停止する。
- 安定した `D<n>`/`AC<n>` IDと、各ACのexact test target/node ID、command、evidence pathをタスク実行から検証まで保持する。
- 固定されたdefault branchとbase commitを要求する。worktreeは
  `wt switch --create <branch> --base <default> --no-cd --format=json` だけで作成し、正規の絶対workdirを解決してすべてのpacketとtoolへ渡す。
- allowlist、artifact revision、不変のレビューsnapshot identityを保持する。hook-trust approval、defaultでないbase、またはprotected-contract判断では停止する。

## 実装routingとreview

- 未完了taskごとに`DIRECT / OPTIONAL_DELEGATION / MANDATORY_SPECIALIST`を再分類する。decision-completeな通常実装はfresh `worker`へ渡し、共通effort-policy.mdでmodel/effortを選ぶ。Controller直行は明確・局所・可逆でprotected contract非該当、委譲コストが作業を上回る小変更だけ。独立contextのbounded packetを固定し、逐次依存、同一mutable worktree、shared fileを並列workerへ渡さない。optional failure後は条件を再確認した場合だけController直行へfallbackする。計画不足はspecification/planningへ戻し、計画が十分でも実装固有の推論が難しい時だけ上位workerへ昇格する。
- 観測可能な変更は `RED -> RED reason -> minimal GREEN -> GREEN confirmation` を要求する。refactor は必要な場合だけ行い、変更後に再検証する。docs・生成物・非挙動設定は理由と代替検証を記録して確認し、形式的な failing test や追加 reviewer 承認を要求しない。
- 全task完了後、固定した単一`review_snapshot_id`へ`~/.codex/review-policy.md`のcanonical risk matrixを1回適用する。同じscopeにtask-reviewerとfinal reviewerを重複起動しない。同じ問題へ異なる修正が2回失敗した場合だけfresh 上位モデル / high `debugging`をmandatoryとし、根拠付き修正条件を得るまでfail closedとする。

## 最終ゲートと引き継ぎ

- canonical matrixが要求するfresh 上位モデル / high `reviewer`へ固定baseの全diffとactive ACを渡す。content、mode、deletion、base、allowlistのいずれかが変わればreviewとlocal validationを全面無効化し、別snapshotの結果を合成しない。
- 記録済みの検証コマンドと実行可能な実入口を実行し、失敗と未検証範囲を記録する。共有 `~/.agents/workflows/software_delivery/references/review-common.md` と `human_review.py` の検査に従い、v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。`check-gates --to LOCAL_COMPLETE` 成功後はコミットせず、次に選べるphaseは `ship-change` だけだと報告する。
- 最終レビューはexact active-AC tableから開始し、`UNSATISFIED` は拒否する。`UNVERIFIED` は理由と予定checkがあれば後続のlocal verification待ちとして許容し、receiptで解消する。Controller は共有契約の review binding・`evidence-run`・`check-gates` 手順を実施する。詳細は共有の `~/.agents/workflows/software_delivery/references/evidence-contract.md` を参照する。`native auto compact` は260,000で透明に扱い、再開はartifact駆動とし、手動handoffをゲートにしない。
- `HERDR_ENV=1` の時は、人間へ結果を提示する直前に `nvim-review-open --base <固定した base>` を 1 回実行する。同じ workspace の nvim に `base..作業ツリー` の diffview を新しいタブで開き、その nvim ペインへフォーカスを移す（nvim が居なければペインを分割して起動する）。差分を見せる先を用意するだけで、待ち方は risk 区分のまま変えない。失敗したら 1 行報告して提示を続け、再試行やペインの後片付けをしない。
- `~/.codex/review-policy.md` に従い、報告だけから進捗を推測しない。
