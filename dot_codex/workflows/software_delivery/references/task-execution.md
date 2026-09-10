# execute-planのタスク実行契約

このreferenceは明示的な`execute-plan` phaseの運用契約です。承認済みの`spec.md`と
`plan.md`、または承認済みのshort-path task artifactを入力し、`LOCAL_COMPLETE`で終了
します。shipping authorityを付与せず、commitも作成しません。

artifactとplanの承認には同じ階層の[`spec-and-plan.md`](spec-and-plan.md)を、state/CAS
recoveryには[`state-recovery.md`](state-recovery.md)を、artifactの所有権には
[`artifact-lifecycle.md`](artifact-lifecycle.md)を、snapshotのidentityと一致確認には
[`review-snapshot.md`](review-snapshot.md)を使います。

## 開始とresumeのゲート

dispatch前にstate helperで`context.json`を検証し、記録されたphase、artifact revision、
execution choice、不変identityを確認します。identityにはsource root、固定されたdefault
branch、完全なbase commit、artifact pathが含まれます。plan review（またはshort-path
preflight）に合格しており、taskのgoal、acceptance criteria、owned paths、evidence、
validation commands、constraints、stop conditionsを読み取れる必要があります。

開始時とresume時に、参照されるすべてのartifactとGit証拠を調べます。worktree pathと
branchが記録済みのもの、baseが記録済みの完全なcommitに解決されること、allowlist外の
変更をtask outputと誤認していないことを確認します。欠落、stale、矛盾、malformed、または
stateより先行したartifact/Git recordがあれば、worker dispatch前にhard stopとします。
`progress.md`、report、command outputは証拠にすぎず、`context.json`がstate authorityです。
state更新にはcompare-and-swap revisionを使います。

最初の未完了gateからresumeします。完了したtaskは決してredispatchしません（not
redispatch）。実装が完了していれば未完了のreviewだけを再実行し、reviewが完了して
いれば未完了のverificationだけを再実行します。未完了の実装taskは、その証拠を再検証
してからredispatchします。commit済みcontext revisionより新しいreportから、完了した
gateを推測してはいけません。

## worktreeゲート

executionはworkflowのdefault branchからだけサポートします。記録された意図したbaseを
Worktrunkのdefaultと比較し、defaultでないbaseまたはbranchはstop conditionです。
execution choiceを記録した後、次のcommandを正確に実行します。

```text
wt switch --create <branch> --base <default> --no-cd --format=json
```

JSONを取得して検証し、選択されたworktreeを存在する正規のabsolute pathへ解決して、
そのpathとbranchを`context.json`へ保存します。すべてのworker、reviewer、debugging
packet、command、toolの`workdir`に同じabsolute pathを渡します。project hookがtrust
approvalを求めたら停止してユーザーに尋ね、`--yes`を追加したりhookを迂回したりしません。
fallbackのworktree commandは使いません。

## task routingと実装

taskはplanの順序どおり処理し、各未完了taskを`DIRECT / OPTIONAL_DELEGATION /
MANDATORY_SPECIALIST`へ分類して根拠を記録します。decision-completeな通常実装はfresh
`worker`へ渡し、model/effortは共通effort-policy.mdで選びます。明確・局所・可逆でprotected
contract非該当、かつ委譲コストが作業を上回る小変更だけControllerが直接実装します。
packetはgoal、acceptance criteria、owned paths、evidence、validation、constraints、
stop conditions、absolute workdirを固定します。workerはcommit、push、外部write、
subagent起動を行いません。逐次依存、同一mutable worktree、shared fileのwriteは並列化しません。

optional workerのunavailable、timeout、無証拠ではoptional条件を再確認してから直接継続を
判断します。計画不足はspecification/planningへ戻し、計画が十分でも実装固有の推論が
難しい時だけ上位workerへ昇格します。曖昧性、protected contract、plan逸脱、競合仮説は
上位specialistへ再分類し、mandatory failureはstopまたはnarrow redispatchとします。

観測可能な挙動変更では、次のsequenceを必須とし、各結果を記録します。

```text
RED -> verify the expected RED reason -> minimal GREEN -> verify GREEN
     -> 必要な refactor を行った場合のみ再検証
```

RED testは実装前に、文書化された理由で失敗しなければなりません。limited refactorは
owned change内の重複を除くか命名を改善するだけとし、挙動や将来向け抽象化を追加しては
いけません。docs、generated artifact、純粋なconfigurationなど非挙動taskは、承認済み
planに対象、非挙動である理由、代替validation commandを記録して検証します。追加の
reviewer承認や形式的なREDを要求しません。挙動変更を非挙動と扱ってはいけません。

各task packetとその証拠は承認済み`D<n>`/`AC<n>`値を保持します。該当する各ACについて、
exact test target/node ID、validation command、evidence pathを記録します。workflow-local
identifierを埋め込むためだけにrepository test名を変更してはいけません。このmappingの
いずれかが欠けていればtaskは未完了です。

## reviewと修正ループ

全task完了後の単一`review_snapshot_id`へ`~/.codex/review-policy.md`のcanonical risk
matrixを1回適用します。同じscopeをtask reviewとfinal reviewで重複確認しません。重要な
Findingにはscenario、impact、一次証拠、最小fixまたはverification、変更deltaを要求し、
修正後は同じsnapshot gateを作り直します。同じissueへの異なるfixが2回失敗した場合だけ
fresh 上位モデル / high `debugging`をmandatoryとし、root causeと修正条件を確定するまでfail closed
とします。

## native compactionとartifact駆動resume

管理されたnative auto compactのthresholdは総token `260,000`です。到達しても透過的に
処理し、手動`/compact`、handoff、新しいsession、phase transitionを要求してはいけません。
contextが失われたりsessionが交代したりした場合は、検証済みartifactからresumeします。
`context.json`がauthorityであり、commit済み証拠が最初の未完了gateを示します。commit済み
revisionより先行したcheckpointやreportを昇格させず、逐次継続の前に直前のcontrollerが
停止していなければなりません。

## 最終acceptance-criteria review

最終verdictの前に完全なactive AC setを作り、最初に次のtableを示します。

```text
AC ID | test/evidence | status
```

tableにはactive ACをそれぞれ正確に1回だけ記載し、statusは`SATISFIED`、`UNSATISFIED`、
`UNVERIFIED`に限定します。Retired IDは別tableに記載し、満足証拠を付けません。active
ACに`UNSATISFIED`が一つでもあればfinal reviewは承認できず、`UNVERIFIED`は理由と予定check
がある場合に限り後続 verification 待ちとして許容します。review 入口と local completion は別の gate です。`LOCAL_COMPLETE` には全 active AC の成功 receipt と現在提示へのユーザー明示承認が必要です。同じAC-to-test/evidence mappingを`verification.md`に保持します。
詳細は共有の `~/.agents/workflows/software_delivery/references/evidence-contract.md` を参照します。

## 最終review、snapshot、ローカル検証

Controller は共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` の phase 手順2–3を実施する。final review 前に `load_contract` で registry を検証し、review 後に file hash・contract hash・snapshot と AC 判定を `evidence.json.review` へ束縛する。`check-gates --to LOCAL_VERIFICATION` を通し、不足 check を `evidence-run` で収集する。共有 `~/.agents/workflows/software_delivery/references/review-common.md` と `human_review.py` の検査に従い、v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。shipping 認可済み composite の引き継ぎは同 reference の D1 に従う。

全task完了後、固定したmerge-baseからのallowlist対象diff全体とactive ACへcanonical risk
matrixを適用します。minorはController self-check、normal/highはfresh 上位モデル / high reviewer
1体、独立Risk triggerは非重複lensのfresh 上位モデル / high reviewer 2体です。verdictは`APPROVED`、
`CHANGES_REQUIRED`、`USER_DECISION_REQUIRED`のいずれかです。

Task 4のsnapshot helperを使い、完全なbase commitと意図したworktree treeから不変の
`review_snapshot_id`（review snapshot identity）を計算します。reviewとローカル
検証を同じsnapshotへ束ねます。content、mode、deletion、allowlist、base、または
external-dirty preflightのいずれかが変われば両gateを無効化して再実行し、別snapshotの
reportを再利用しません。

`APPROVED`のfinal review後、同じsnapshot・入力・環境の成功evidenceを確認し、
不足するvalidation commandと未確認のreal entry pointだけを固定したabsolute workdirで実行します。exact command、成功、失敗履歴、
未検証scopeをverification artifactに記録し、stateは`context.json`だけで進めます。失敗
したら所有するtask、review、verification gateへ戻し、gateをskipする理由にはしません。

`verification.md`は正準見出し（行頭が`#`の行）を2種持ちます — 失敗履歴側の見出しに
`失敗`または`Failure`、未検証scope側の見出しに`未検証`/`未実施`/`未確認`のいずれかを
含めます。
どちらかが欠けると`LOCAL_VERIFICATION -> LOCAL_COMPLETE`（および`-> COMMIT`）が
`artifact lint failed`でrc=1になり`context.json`は変更しません（検査の詳細は
[`state-recovery.md`](state-recovery.md)のartifact syntax presence lint）。

検証成功後、v2 LOWは人間待ちなし、MEDIUM/HIGHは現在提示への明示承認、v1 legacyは従来承認とし、helper検査成功を確認してsnapshotを記録し、`LOCAL_COMPLETE`へ遷移します。`execute-plan`の
選択はローカル完了だけを意味し、commitは作成せず、stage、push、MRのopen/変更、merge、
release、tag、外部書き込みを行いません。結果を報告し、次のphase（次のoptional phase）
として明示的な`ship-change`を示します。shipping authorization 記録済みの `execute-and-ship` composite は、この handoff または共有 evidence contract の D1 による `LOCAL_VERIFICATION` handoff を使います。

## 停止とrecoveryの条件

defaultでないbase、未承認Worktrunk hook、欠落または不整合なartifact/Git証拠、stale
revision、snapshot不一致、未解決の重要Finding、protected-contractまたはsecurityの判断、
scope拡大、信頼できないvalidationがあればdispatch前に停止します。調査できるよう
worktreeとartifactを保持します。後でresumeするときは記録済みcontextとGit stateを再検証し、
完了済みtask履歴を保持して最初の未完了gateだけを続けます。部分的に書かれたfileやreport
から進捗を推測してはいけません。
