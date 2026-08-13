---
name: post-merge-cleanup
description: MR が merge された後に、workflow が作った Worktrunk worktree を安全に削除する時に使う。「後片付けして」「worktree を消して」「merge したので掃除して」などで、ユーザーが明示的に依頼した時だけ起動する。workflow artifact は削除せず残す。merge 前の出荷（ship-change）や、merge そのものには使わない。
---

# Post-Merge Cleanup

workflow が所有する worktree を削除して workflow を終端させる phase。**ユーザーの明示依頼**があり、かつ forge 上で MR が **merge 済み**であることを確認した後にだけ走る。

**`.aidocs/workflows/<workflow-id>/` の artifact は削除しない。** spec / plan / review / verification / progress は、この workflow で何をどう決めてどう検証したかの唯一の記録で、merge 後も参照される。`.aidocs/` は `.git/info/exclude` により Git 追跡外なので、残してもリポジトリを汚さない。削除するのは worktree（と Worktrunk が付随して消す local branch）だけ。

契約の詳細は [references/cleanup.md](references/cleanup.md)、state と helper CLI は `~/.claude/skills/execute-plan/references/state-and-artifacts.md` にある。

## 事前確認

`context.json` から正確な branch、canonical な worktree path、artifact root、所有関係、対象 workflow を読み取り、**削除対象を先に列挙**する。entry と resume で state と evidence を検証する。merge 済みかは forge 側（`gh`）で確認し、報告や推測で代替しない。所有関係の不一致は停止してすべてを保持する。

## worktree 内の記録を先に退避する

worktree の中にしか無いファイルは worktree ごと消える。削除の**前に**、次を親リポジトリの `.aidocs/workflows/<workflow-id>/` へ写す。

- `<worktree>/.git` が指す worktree 専用 git dir（`git rev-parse --path-format=absolute --git-dir`）配下の `harness-evidence.jsonl` → artifact 配下の `evidence.jsonl` へ追記
- その worktree でしか作っていない検証ログ・計測結果・スクリーンショット等（`.gitignore` されていて commit に乗らなかったもの）

古い記録が worktree 側に残っている場合にだけ退避が要る。退避できたことを確認してから削除へ進む。

## Worktrunk による削除

repository の primary worktree から、次を**そのまま**実行して stdout を保存する。

```text
wt remove --foreground --format=json <branch> > wt-remove.json
```

`--force`、`-D`（`--force-delete`）、`--no-hooks`、`--yes`（`-y`）を**付けない**。command を書き換えない。dirty な worktree、未 merge / 移動した branch、未承認の hook は stop condition で、その場合はすべてを保持する。`git worktree remove`、branch 削除、`rm` などの破壊的な fallback へ切り替えない。

local master が merge を取り込む前だと Worktrunk は branch を「unmerged」と判定して worktree だけ消す。その場合は `git fetch` で親リポジトリの default branch を進めてから**同じ command をもう一度**実行する（`-D` を付けない）。

## 削除の確認

削除できたことを Git 側で直接確認する。Worktrunk の JSON は version 間でスキーマが変わる（v0.71.0 は `branch_deleted` を返し、worktree 削除と branch 削除が別 record に分かれる）ので、JSON の形だけを根拠にしない。

```text
git worktree list                 # 対象 path が消えていること
git branch --list <branch>        # 出力が空であること
```

どちらかが残っていれば非終端。原因を報告して停止し、強制削除へ切り替えない。

## 終端

確認できたら `workflow_state.py` で `WT_REMOVE` へ expected revision 付きで遷移し、artifact を残したまま終端状態を報告する。**`ARTIFACT_REMOVE` へは進めない。`workflow_artifact.py remove` を呼ばない。** 終端後に次の skill を案内しない。

## この phase が行わないこと

merge、release、tag、production 変更はしない。**remote branch を削除しない。workflow artifact を削除しない。** merge 前に cleanup を走らせない。報告だけから削除を推論しない。強制削除の flag や fallback command を使わない。
