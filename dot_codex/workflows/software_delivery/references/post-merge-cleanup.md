# マージ後クリーンアップの引き継ぎ

マージ後のクリーンアップは、ユーザーが明示的に要求し、かつforgeがworkflowの
merge requestをmergedと確認した後だけ実行します。何かを削除する前に、schema-v1
`context.json`から正確なbranch、正規worktree path、成果物directoryを記録します。

削除するのはworktreeだけです（Worktrunkがそれと一緒に削除するlocal branchを含む）。
`.aidocs/workflows/<workflow-id>/`配下のartifactにはspec、plan、review、検証記録が
保持され、merge後も参照されるため、そのまま残します。

`identity.artifact_root`が削除予定のworktree内にある場合はstop conditionです。
worktreeを削除するとworkflow自身の記録を壊すため、何も削除せず、成果物の場所と
その状態になった経緯を人間の判断用に報告します。worktree内からworkflowを開始
するとこの状態になります。

## worktreeだけにある記録の救出

worktree内にしか存在しないファイルはworktreeとともに消えます。削除する*前に*、
親リポジトリの`.aidocs/workflows/<workflow-id>/`へコピーしてください。対象は、
worktree専用git dirの`harness-evidence.jsonl`（`git -C <worktree> rev-parse
--path-format=absolute --git-dir`で解決し、既存行を重複させずartifactの
`evidence.jsonl`へ追記）と、commitに入っていない検証ログや出力です。
救出できないものがあれば停止して報告します。

## Worktrunkによる削除

削除前に固定artifactの `evidence/cleanup/` へ `workflow_artifact.py evidence-export --context PATH --output <固定ART>/evidence/cleanup` を実行し、`workflow_state.py check-gates --context PATH --to WT_REMOVE` で証拠を検査する。共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` に従い、`human_review.py --context PATH` の現在risk gateと保持 record の一致も検査する。既存bundleがstaleなら、旧bundleを保持したまま新directoryへexportして検査後に置き換える。成功後にだけ、以下の既存削除手順とGit確認、`WT_REMOVE` 遷移を行う。

まず対象リソースを列挙し、リポジトリのprimary worktreeから次のコマンドをそのまま
実行します。コマンドを変更したりflagを追加したりせず、stdoutを保存します。

```text
wt remove --foreground --format=json <branch> > wt-remove.json
```

このcommandでは`--force`、`-D`（または`--force-delete`）、`--no-hooks`、
`--yes`（または`-y`）を使ってはいけません。dirtyなworktree、unmergedまたは
移動したbranch、未承認のhookはstop conditionです。`git worktree remove`、
branch削除、`rm`、その他の破壊的なcleanup commandへフォールバックしません。

local default branchがまだmergeを取り込んでいない場合、Worktrunkはbranchを
unmergedと報告し、worktreeを削除してbranchを残します。親リポジトリのdefault
branchを`git fetch`で進め、同じcommandをもう一度実行します。決して`-D`に頼りません。
default branchの履歴に本当に含まれないbranchはstop conditionです。

## 結果ゲート

保存したJSONではなく、Gitに対して削除を確認します。

```text
git worktree list                 # the canonical worktree path is gone
git branch --list <branch>        # the output is empty
```

WorktrunkのJSON schemaはversion間で変わります。v0.71.0は
`{"branch","branch_checked_out_at","branch_deleted","kind","path"}`を返し、
worktree削除とbranch削除を別runの別recordに分けます。そのためhelperはこれを検証
せず、shapeを削除のverdictに使いません。`wt-remove.json`は証拠としてのみartifact
へ保存します。

終端成功には両方のcheckが必要です。それ以外はnonterminalです。保持されたbranch、
unmergedまたはchecked-outのbranch、deferredまたは`not_attempted`の削除、無効なJSON、
`context.json`との不一致があれば、調査または後日のretryのためworktreeとartifactを
保留し、何も削除しません。forced removalへエスカレーションしないでください。

## 終端状態

両方のGit checkが通った後だけ、controllerは`workflow_state.py`を使い、期待する
artifact revisionでcontextを`WT_REMOVE`へ遷移させ、`workspace.worktree_path`を
nullに設定できます。`WT_REMOVE`はこのphaseの終端状態です。`ARTIFACT_REMOVE`へ
進めたり、`workflow_artifact.py remove`を呼び出したりしません。このedgeはworkflow
記録を削除する別の明示的なユーザー要求のためだけにstate machineへ残っています。
remote branchの削除はこの引き継ぎの範囲外であり、forge workflowが別途認可しない
限り実行しません。
