---
name: post-merge-cleanup
description: 明示的な認可とMRのマージ確認後に、artifactを保持したままworkflow所有のWorktrunk worktreeを安全に削除する。
---

# マージ後のクリーンアップ

明示的なユーザー依頼後のみ実行する。forge上のMRがマージ済みであること、
`context.json` が正確なブランチ、正規worktree、artifact root、所有権、想定workflowを証明することを確認する。削除前に対象リソースを列挙し、開始時または再開時に状態と証拠を検証する。

worktreeだけを削除する（Worktrunkが併せて削除するローカルブランチを含む）。
`.aidocs/workflows/<workflow-id>/` 配下のartifactが決定・検証内容の唯一の記録なので保持する。worktree内にしか存在しないものは、削除前にartifactへ退避する。

リポジトリのprimary worktreeから、次のコマンドを正確に実行する。

```text
wt remove --foreground --format=json <branch>
```

そのJSONを保存するが、`--force`、`-D`、`--no-hooks`、`--yes`、または代替の削除コマンドは使わない。`dirty`/`unmerged`/`moved branch`、`hook trust request`、所有権不一致があれば停止し、すべてを保持する。

削除確認はそのJSONではなくGitで行う。`git worktree list` に正規pathが表示されなくなり、`git branch --list <branch>` が空でなければならない。Worktrunkのschemaはversion間で変わるため、保存結果は証拠にすぎず削除判定には使わない。その他（保持または未マージのブランチ、`deferred` または `not_attempted` の削除、無効なJSON、不一致）は `nonterminal` としてすべてを保留し、何も削除しない。確認済みの削除だけを、期待するrevisionで `workflow_state.py` 経由の `WT_REMOVE` へ遷移させる。
`ARTIFACT_REMOVE` へ進めたり、Task 3の `workflow_artifact.py remove` を呼び出したりしない。`WT_REMOVE` がこのphaseのterminal stateである。

remote branchの削除はこの引き継ぎの範囲外なので削除しない。worktree削除に成功したらterminal stateと次のskillがないことを報告する。マージ前にcleanupを実行したり、報告だけから削除を推測したりしない。実行前に
[post-merge-cleanup.md](../../workflows/software_delivery/references/post-merge-cleanup.md),
[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md),
および `~/.codex/review-policy.md` を読む。
