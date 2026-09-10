# ワークフロー状態と復旧

`context.json`はsoftware-delivery workflowにおける唯一の機械可読state authorityです。
report、`progress.md`、command outputは証拠であり、それだけでworkflowを進めては
いけません。

## schema v1

文書には次の必須objectが含まれます。

- `identity`: `schema_version` (`1`)、`workflow_id`、`source_root`、
  `artifact_root`、`default_branch`、および`base_commit`。
- `workspace`: nullを許容する`worktree_path`と`branch`。
- `state`: `phase`、nullを許容する`stopped_from`、および非負の
  `artifact_revision`。
- `authorization`: `shipping_authorized`.
- `artifacts`: `spec_path`、nullを許容する`plan_path`、`tasks_path`、`reviews_path`、
  および`verification_path`。
- `execution`: task record、gate record、nullを許容する実行`choice`、および
  nullを許容する`review_snapshot_id`。
- `shipping`: nullを許容する`commit`、`push`、`mr`、および`ci`のstatus値。

初期化後、identityは不変です。state graphには`DISCOVERY`から`ARTIFACT_REMOVE`まで、
short-path phaseの`SHORT_TASK_DRAFT`と`SHORT_TASK_PREFLIGHT`、さらに`DEBUGGING`と
`USER_DECISION_REQUIRED`が含まれ、`STOPPED` phaseはありません。short-pathのedgeは
`DISCOVERY -> SHORT_TASK_DRAFT`、`SHORT_TASK_DRAFT -> SHORT_TASK_PREFLIGHT`、
`SHORT_TASK_PREFLIGHT -> EXECUTION_CHOICE`です。redraftは`SHORT_TASK_DRAFT`へ戻り、
normative gapは`DISCOVERY`へ戻り、blockerは`USER_DECISION_REQUIRED`へ向かいます。
外部blockerには`stop`を使い、直前のphaseを`state.stopped_from`へ記録し、`resume`で
そのphaseを復元します。`stopped_from`のないuser-decision stateはresumeできないため、
適切なnormativeまたはcontroller gateで解決します。

## discoveryの選択と逐次resume

新規requestは新しいworkflowを作り、保持されたterminal artifactを自動resumeしません。
明示されたworkflow ID/pathは直接検証します。指定がなければnonterminal workflowだけを
候補にし、曖昧さのない候補が一つの場合だけ自動選択します。複数候補ではユーザーに
一つを選んでもらいます。resumeではidentity、schema、phase、revision、source root、
commit済みartifact/Git証拠を検証し、最初の未完了のcommit済みgateから続けます。
直前のcontrollerがそのworkflowの操作を停止していることを前提にします。別controllerが
liveである証拠があれば継続を拒否します。concurrent controllerはunsupportedであり、
この契約はmulti-writer検出やlock protocolを追加しません。

## native compactionとartifact駆動resume

native auto compactは管理された総token `260,000`のthresholdで引き続き有効です。
thresholdに達しても手動`/compact`、handoff prompt、新しいsession、workflow phaseの変更を要求してはいけません。compactionはruntime上の関心事であり、sessionを意図的に
交代または中断した場合のrecoveryはartifact駆動かつ逐次的に行います。

resume時は`context.json`を検証し、commit済みrevisionとartifactのcommit済み証拠を
使って現在のphaseと次のgateを再構成します。欠落したcheckpoint、部分的な書き込み、
stateより先行した証拠から進捗を推測してはいけません。別sessionがworkflowを続ける前に、
直前のcontrollerが停止していなければなりません。

## gateの証拠とbounded checkpoint

controllerだけがworkflow-artifactを書き込みます。承認したdecisionまたは完了したgate
ごとに、まず証拠を書いて検証し、CAS commit（`context.json`のcompare-and-swap）でgateを
commitしてから、`progress.md`へbounded checkpointを一つ追記します。checkpointは証拠で
ありstate authorityではありません。workflow ID、phaseとrevision、完了したgate、承認済み`D<n>`の値、関連する`AC<n>` status、未決のdecisionまたはblocker、次のgate、
artifact/evidence pathを記録します。

checkpointの追記に失敗したら失敗を報告します。権威あるCAS commitはrollbackせず、
この追記失敗はstate rollbackではありません。resume時は`context.json`とcommit済みartifact evidenceから欠落したcheckpointを再構成します。commit済みstateより先行した
証拠（ahead-of-state evidence）はgateを進めてはならず、隔離または置換できます。

## CLI契約

すべてのcommandには`--context <path>`が必要です。

```text
workflow_state.py validate --context context.json
workflow_state.py transition --context context.json \
  --expected-revision N --to PHASE [--patch-json JSON_OBJECT]
workflow_state.py invalidate-normative --context context.json \
  --expected-revision N
workflow_state.py stop --context context.json --expected-revision N \
  --reason "external blocker"
workflow_state.py resume --context context.json --expected-revision N
```

成功するmutationはすべてcompare-and-swapです。指定revisionは
`state.artifact_revision`と等しく、結果のrevisionは必ず1だけ増えます。無効なJSON、
必須fieldの欠落、無効なtransition、不変identityの変更、stale revision、`artifact lint
failed`（下記のartifact syntax presence lint不合格）はいずれもnonzeroで終了し、元のbyte
列を変更しません。

### artifact syntax presence lint

`transition`は特定のedgeで、gateを裏付けるartifactに最低限の構文的痕跡があるかを機械
検査します（内容の当否は判定しません）。不合格ならstderrに`error: artifact lint failed`から
始まるblockを出し、不足を**全件**（1件につき不足行1行と`期待例:`1行）列挙してrc=1で終了し、
`context.json`は変更しません。
pathは`--context`が指す`context.json`の親directoryからの固定相対pathで、
`artifacts.*_path`も`identity.artifact_root`も`--patch-json`も参照しません。

| edge | 検査 |
| --- | --- |
| `SPEC_REVIEWS -> USER_APPROVED_SPEC` | L1 |
| `FINAL_REVIEW -> LOCAL_VERIFICATION` | L1 + L2 |
| `LOCAL_VERIFICATION -> LOCAL_COMPLETE` | L1 + L3 |
| `LOCAL_VERIFICATION -> COMMIT` | L1 + L3 |
| `LOCAL_COMPLETE -> COMMIT` | L1 + L3 |

- L1: `spec.md`に`AC[ \-_]?[0-9]+`にマッチするAC識別子を含む行が1行以上。short path
  （`tasks/01-short-path.md`が**regular file として**存在し`spec.md`がL1を満たさない。symlinkやdirectoryのmarkerでは免除しません）ではすべてのedgeで免除
  されます。
- L2: `reviews/final-review.md`にAC識別子と`SATISFIED`/`UNSATISFIED`/`UNVERIFIED`のいずれ
  かを同一行に含む行が1行以上。lint対象artifactの正本は
  [`artifact-lifecycle.md`](artifact-lifecycle.md)を参照します。
- L3: `verification.md`に、`失敗`または`Failure`を含む見出し（行頭が`#`の行）と、
  `未検証`/`未実施`/`未確認`のいずれかを含む見出しが各1つ以上（詳細は
  [`task-execution.md`](task-execution.md)）。

`invalidate-normative`は`SPEC_REVIEWS`へ移し、`plan_path`を削除し、activeな
`execution.tasks` mapをクリアし、planと下流gateの値をクリアし、execution choiceと
snapshotをクリアし、shipping authorizationを取り消し、shipping statusをリセット
します。active task IDを置き換えplanへ持ち越してはいけません。監査履歴は追記専用の
`progress.md`または別のhistory/audit fieldに置き、そうした別fieldはinvalidationで
変更しません。

## atomic commit pointとrecovery

mutationではhelperが完全な次のcontextをcontext directory内の一意な名前のtemporary
fileへserializeし、そのfileをflushして`fsync`してから`os.replace`で`context.json`へ
置き換えます。replaceの成功がcommit pointです。replace前の書き込み失敗や中断では
temporary fileを削除し、以前のcontextをbyte-for-byteで変更しないままにします。

完全なload、revision compare、operation、replaceのsequenceは、包含directory inodeに
対するadvisoryな`fcntl.flock` exclusive lockの下で行います。置換されるcontext inode
ではなくdirectoryをlockすることで、`os.replace`をまたいでもlockが安定します。lock
fileは作成も削除もしません。そのため2番目のwriterは待機後に新たにcommitされたrevision
を読み、compare-and-swapをstaleとして失敗させます。

中断後のresumeでは`context.json`を読み検証し、記録済みartifactとGit証拠を調べ、最後に
atomic commitされたrevisionだけを信頼します。部分的に書かれたtemp fileやcontextより
先行したevidence reportから、より後のstateを推測してはいけません。

## 人間レビューの停止と再開

`execution.human_review` は共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` に従う optional な typed record。旧v1 contextは読取/停止/修復できるが、完了・shipping・cleanupには従来の現在提示への明示承認が必要。v2 LOWは人間待ちなし、MEDIUM/HIGHはriskに応じた明示承認とする。`human_review.py --context PATH` で欠落・部分回答・stale・撤回を再検査し、`execution.gates` の手書き passed で代替しない。

present は `USER_DECISION_REQUIRED` に停止する。respond 成功後も停止を保つため、最新 artifact revision で既存 resume を実行する。承認済みでも snapshot・判断・検証前提・証跡が変われば再判定/再提示し、単なる resume や予定済み CI 成功では承認を反復しない。完了後の revoke は同じ CAS 内で停止する。cleanup では保持 record と live record を照合し、再承認後は新 export を検査して保持 bundle を更新してから resume する。`LOCAL_VERIFICATION` の入口と `TASKS` / `DEBUGGING` / `SPEC_REVIEWS` への回復に、完了承認を要求しない。
