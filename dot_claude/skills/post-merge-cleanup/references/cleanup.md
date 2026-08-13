# post-merge cleanup の契約

`post-merge-cleanup` の運用契約。**ユーザーの明示依頼**があり、かつ forge 上で MR が merge 済みであることを確認した後にだけ走る。**削除するのは worktree（と Worktrunk が付随して消す local branch）だけで、workflow artifact は残す。**

- state と helper CLI: `~/.claude/skills/execute-plan/references/state-and-artifacts.md`

## 事前確認

削除の前に、schema-v1 `context.json` から正確な branch、canonical な worktree path、artifact root、所有関係、対象 workflow を読み取り、**削除対象の resource を先に列挙**する。entry と resume で state と evidence を検証する。MR が merge 済みであることは forge 側（`gh`）で確認し、報告や推測で代替しない。

## worktree 内の記録の退避

worktree の中にしか無いファイルは worktree ごと消える。削除の**前に**親リポジトリの `.aidocs/workflows/<workflow-id>/` へ写す。

| 対象 | 退避先 |
|---|---|
| worktree 専用 git dir 配下の `harness-evidence.jsonl` | artifact 配下の `evidence.jsonl` へ追記（既存行と重複させない） |
| その worktree でしか作っていない検証ログ・計測結果・成果物のうち commit に乗らなかったもの | artifact 配下 |

worktree 専用 git dir は `git -C <worktree> rev-parse --path-format=absolute --git-dir` で解決する（`--git-common-dir` は親リポジトリを指すので退避元の判定には使わない）。退避が済んだことを確認してから削除へ進む。退避できないもの（読めない・場所が特定できない）があれば停止して報告する。

## Worktrunk による削除

repository の primary worktree から、次を**そのまま**実行して stdout を保存する。

```text
wt remove --foreground --format=json <branch> > wt-remove.json
```

`--force`、`-D`（`--force-delete`）、`--no-hooks`、`--yes`（`-y`）を付けない。command を書き換えない。dirty な worktree、未承認の hook、所有関係の不一致は stop condition で、その場合はすべてを保持する。`git worktree remove`、branch 削除、`rm`、その他の破壊的な fallback へ切り替えない。

local の default branch がまだ merge を取り込んでいないと、Worktrunk は branch を「unmerged」と判定して worktree だけ削除し branch を残す。その場合は親リポジトリで `git fetch` して default branch を進め、**同じ command をもう一度**実行する。`-D` で強制削除しない。branch が本当に統合されていない（default branch の履歴に含まれない）なら、それは stop condition。

## 削除の確認

Worktrunk の JSON 出力はスキーマが version 間で変わる。v0.71.0 は `{"branch","branch_checked_out_at","branch_deleted","kind","path"}` を返し、worktree 削除と branch 削除が別々の record（別々の実行）に分かれる。**JSON の形だけを削除の根拠にしない。**

削除は Git 側で直接確認する。

```text
git worktree list                 # canonical な worktree path が消えていること
git branch --list <branch>        # 出力が空であること
```

両方を満たした時だけ終端成功。片方でも残っていれば非終端で、原因を報告して停止する。保存した `wt-remove.json` は evidence として artifact 配下に置くだけで、判定の根拠にはしない。

## 終端

確認できたら `workflow_state.py` で `WT_REMOVE` へ expected revision 付きで遷移し、`workspace.worktree_path` を null にする。**artifact は残すので `ARTIFACT_REMOVE` へは進めず、`workflow_artifact.py remove` も呼ばない。** `WT_REMOVE` がこの phase の終端で、artifact は merge 後の参照用に残る。

remote branch の削除はこの handoff の外なので**行わない**（forge 側の workflow で別途認可された場合のみ）。終端したら状態を報告し、次の skill を案内しない。merge 前に cleanup を走らせない。報告だけから削除を推論しない。
