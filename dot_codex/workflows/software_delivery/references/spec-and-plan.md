# 仕様と計画の契約

discovery 担当は spec（short path は task）に `| AC ID | Lifecycle | Criterion |` の canonical table を1つ作る。Controller は plan 確定後（short path は task 確定後）に `evidence.json` を登録し、final review 前に source と registry を照合する。review 後の binding、local verification の collector、各 gate の担当・時点・schema は共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` の phase 手順に従う。

この契約は artifact を初期化した正式 workflow に適用する。明確な局所変更は初期化前に共通 effort-policy.md の直接完了条件で扱う。既存 workflow / active AC を途中から直接経路へ落とさず、承認・外部サーフェス・snapshot・shipping gate を保持する。


このreferenceは`product-discovery`と`implementation-planning`で共有します。
`.aidocs/workflows/<workflow-id>/`配下のworkflow artifactが永続的な引き継ぎです。
`context.json`は機械可読なstate authorityであり、`spec.md`、`plan.md`、
`reviews/`、`tasks/`、`progress.md`は証拠と引き継ぎのartifactです。reportだけで
phaseを進めてはいけません。

## discovery packetと仕様

controllerはrequest、リポジトリの証拠、現在の挙動、ユーザーの決定、仮定、未知の
事項をevidence packetに記録します。仕様は事実、推論、仮定、未決の判断を分離し、
次を含めなければなりません。

- Goal/users、context、constraints、scope、non-goals
- normativeな外部挙動、main flow、state/error/permission/boundaryの規則、
  compatibility/protected-contractの制約
- Given/When/Then acceptance criteria、検証証拠、仮定、およびscope内の結果を
  変え得る未解決の判断がないこと

ユーザーに問うproduct decisionは、次のすべてを満たすものだけです。

1. repository evidence、明示済みの制約、accepted decisionから一意に導けない。
2. 選択によってユーザーから観測できる結果、scope、protected contractのいずれかが変わる。
3. productの価値判断またはユーザーの優先順位が必要である。

既存挙動の継承、accepted non-goalの帰結、generator/frameworkの標準挙動、
観測可能な契約を変えない実装選択は、事実、導出制約、またはimplementation noteとして
記録し、`D<n>`やopen decisionを作りません。コード、テスト、docs、schema、public interfaceから
見つけられる事実をユーザーへ尋ねてはいけません。

依存するproduct decisionは依存順に原則1問だけ行います。独立したdecisionは、それぞれに
2〜3個の選択肢、推奨案、トレードオフを付け、最大3件まで一括確認できます。回答を記録して
下流の依存関係を再評価します。

## 安定したdecisionとacceptanceの追跡性

workflow内でdecision identifier `D<n>`とacceptance-criterion identifier `AC<n>`を
単調に割り当てます。各identifierは並べ替え、resume、compaction、後続sessionを
またいで安定させ、割り当て済みidentifierをrenumberまたはreuseしません。すべての
active decisionにはreasonを記録します。decisionやcriterionを削除するときは、その
identifierを処置と満足証拠なしの`RETIRED` tombstoneとして保持します。retired
identifierはactive setの一部ではなくgateの承認に使えません。後のcriterionの文言が
似ていてもretired identifierを再利用しません。

specification agentはユーザーに代わってproduct decisionをせず、identifierとreasonを
出力します。planning agentは同じidentifierを引き継ぎ、置き換えを新設したり、
renumberしたり、対応する証拠のないproseから完了を推測したりしてはいけません。

### 仕様review

draft完成後は`~/.codex/review-policy.md`のcanonical risk matrixを適用します。minorは
Controller self-check、normal/highはfresh 上位モデル / high reviewer 1体、独立Risk triggerは
非重複lensのfresh 上位モデル / high reviewer 2体です。phase名やartifact名だけで人数を固定しません。
複数reviewerには同じscopeと証拠を渡しますが、互いのprompt、結論、Findingを共有しません。

Completenessは浅いkeywordや新しいreviewer typeではなく、適用可能な具体的checklistを
一つ使います。scope内の各懸念について、state authorityとtransition、integration
seam、invariant、partial failure、resume/retry、observability、rollout、migration、
recoveryを確認します。`## 外部サーフェス`節が本文の決定を漏れなく拾っているか、本文と
食い違っていないかも確認します。公開APIや一般的な後方互換性はcanonical matrixの
high-risk triggerとして扱い、独立Risk triggerへ自動昇格しません。独立reviewは攻撃者視点
またはfailure analysisの独立性を実質的に損なう場合だけ2体に分離します。各reviewerは
割り当てたlensごとに結果を分けて返します。

spec本文から、新しいAPI/endpoint/table/migration/config option/resident process
（worker、poller、cron、daemon）を追加すること、または既存機構にbranch/state/retry/
timeoutを積み上げることが分かる場合、Simplicity reviewerはFindingに少なくとも一つ
の代替案を含めなければなりません。各代替案には既存機構の一次証拠（`file:line`）と、
維持する結果またはprotected contractが必要であり、それらなしで報告してはいけません。
spec本文がその判断を支えない場合、この義務は適用しません。代替案が成立しない場合も
Findingを無理に作らず、`未検証事項`またはreport末尾に理由とともに「代替なし」と記載
します。

各reviewerは証拠、影響、最小の修正または検証、verdictを含むFindingを返します。
controllerはすべてのFindingを、reason付きの`adopted`、`rejected`、または
`user_decision_required`として記録し、結論を黙って統合しません。normative gapはdiscovery/
specificationへ戻します。reviewを反映したspecをユーザーが明示承認するまでplanningへ
引き継がず、その承認を記録します。

### 変更後のclosure review

review後の変更は、controllerが変更前後と依存関係を一次証拠で確認し、次に分類します。

| 変更種別 | 必要なreview |
| --- | --- |
| 誤字、整理、意味を変えない表現変更 | controllerの整合確認だけ。reviewerは起動しない |
| adopted Findingに対するboundedな修正 | そのFinding、変更したID、そのdependency coneだけをclosure review |
| `D<n>` / normative requirement / `AC<n>` / surface familyの局所的な変更 | 変更ID、そのdependency cone、対応する未解決Findingだけを担当lensがclosure review |
| Goal、主要flow、不変条件、権限境界、trust boundary、migration、並行/分散状態、またはprotected contractの境界を拡大する変更 | 影響する初回lensを再実行。中心的なoutcomeまたは採用案が変わるならspec review全体を無効化 |

`dependency cone`は、変更点から依存関係を推移的に辿り、normativeな結果、`AC<n>`、または
surface contractが変わり得るID / familyを含む範囲です。各依存辺を一次証拠で辿ります。
結果が変わらないと証明できた地点で探索を止め、到達不能な独立領域は含めません。例えば
`D1 -> D2 -> AC3 / Surface A`なら末端まで含め、`D1`から到達不能な`D4`は含めません。

closure review packetには変更前後の該当節、変更したstable ID、そのdependency cone、解消対象の
Finding、影響する外部サーフェスだけを渡します。reviewerはそのconeで新たに到達可能になった
問題を報告できますが、未変更の独立した領域を再reviewしません。closureを確認するためだけの
追加final checkは起動しません。変更種別、dependency cone、起動または省略したlensと理由を
`progress.md`へ記録します。

## acceptanceの追跡性

承認済み仕様のaccepted `D<n>` reasonとactive `AC<n>` setが、planningとfinal
verificationのsource identifierです。各plan taskはこれらのdecisionを保持し、`AC ID`を
記録して、該当するすべてのACをexact test target/node ID（workflow-local numberを埋める
ためにrepository test名を変更しない）、それを実行するcommand、結果を記録するevidence
pathへ対応付けます。このmappingはtask artifact、test result、verification、final
review tableに保持します。mappingがない場合はgate未完了です。retired identifierは別tableに
記載し、満足証拠を付けません。

## planning packetとplan

planningは明示的に承認されたspecとその証拠だけを入力にします。名前付きの
上位モデルの`planning` agent（既存決定の転記だけならController）が、実質的な選択が残る場合だけ案を比較し、サポートされる最小の案を選び、
順序付きplanを出力します。planは下位モデルのworkerにとって**decision-complete**であり、
productやarchitectureを再設計しません。

独立してreviewできる各vertical-slice taskには次を記録します。

| field | 要件 |
| --- | --- |
| goal | 観測可能な一つの結果 |
| owned paths | workerが変更できる正確なfile/directory |
| deliverables | code/docs/testsまたは機械的な出力 |
| dependencies | prior task、証拠、順序 |
| interfaces | input/output、symbol、外部boundary |
| acceptance criteria | 客観的なGiven/When/Thenまたは同等の条件 |
| validation | exact commandと期待結果 |
| RED reason | 実装前にfocused testが失敗すべき理由 |
| stop conditions | conflict、protected contract、scope、または信頼できないvalidation |

task内部は所要時間で刻まず、必要な判断と完了条件を示し、test target、期待するRED reason、command、
最小の実装boundaryを持たせます。production code全文を貼り付けたり、共通の
RED/GREEN/refactor手順を各taskで重複させたりしません。

### plan reviewと実行選択

spec、plan、証拠へcanonical risk matrixを適用します。Controllerは常にspec coverage、
scope、decision completeness、dependencies、interfaces、verification feasibilityを検査し、
matrixが要求する場合だけfresh 上位モデル / high reviewerを起動します。Findingは
adopted/rejected/user-decisionとして記録し、normative gapはplanで補わず
`product-discovery`へ戻します。review gateの後は「既存の実行依頼」に従い、未選択の場合だけ次の選択を求めます。

- `execute-plan`：task、review、ローカル検証を実行して停止
- `execute-and-ship`：同じ処理を行い、別途認可されたcommit、push、MR、scope内CIの
  flowへ進む

この選択が追加するのはshipping authorityだけで、承認済みscopeは拡大しないと説明します。
選択が記録される前に実装を開始してはいけません（実装を開始しない）。

## 外部サーフェス合意

`product-discovery`は仕様相当artifact（通常経路は`spec.md`、短縮経路は
`tasks/01-short-path.md`）を書くとき、必ず`## 外部サーフェス`節を持たせます。本体は
判断可能な単位へまとめた`surface family`の一覧と契約カード、または
「外部サーフェスの新設・変更・廃止なし」の1行（ゼロ件宣言）のいずれかにします。

| # | surface family | 区分 | 主要な変更 | 根拠 |
| --- | --- | --- | --- | --- |
| 先頭からの連番（1始まり） | 同じ主契約として一括判断できる名前 | 新設 / 変更 / 廃止 | 変更前から変更後への要約 | そう決めた理由1行 |

`#`は提示のたびに先頭から振り直します（安定IDは作りません）。変更指示は直前に
提示した番号を指すものとして解釈し、行の増減で番号が変わった場合は再提示時に
その旨を1行添えます。

対象にするかどうかの判定基準は次の2つです。

1. この変更で新しく増える・変わる・無くなる、ユーザーまたは他コンポーネントが名前で
   参照するもの。
2. 名前が変わらなくても、外部から観測できる挙動・失敗・互換性の契約が変わるもの。

代表例（閉じた集合ではありません）: API/CLIのシグネチャ、設定キーと既定値、環境変数、
出力・ファイル形式、DB schema、公開型、ファイル配置とパス、キーバインド、エージェント
自身の停止条件やユーザーへの提示形式。基準を満たすか判断できない候補は載せる側に
倒します。

### surface familyと派生artifact

同じ主契約から一意に派生し、独立したproduct decisionを持たないものは同じsurface familyへ
まとめます。例えばruntime API behaviorと、それを同じ内容へ同期するOpenAPI、generated client、
CHANGELOG、release noteは、独立した公開名、shape、compatibility、または選択がない限り
別familyに分けません。同期先は契約カードの「派生artifact / 同期先」として明示します。

別familyに分けるのは、それ単体でユーザーが異なる選択をできる、別の互換性・権限・
ライフサイクルを持つ、または別の失敗とrollbackを独立して合意する必要がある場合だけです。

### 判断可能な契約カード

各familyに`### Surface #<n>: <name>`という契約カードを作ります。カードだけを読めば
合意または変更指示ができるよう、次を含めます。

- 目的と主サーフェス名、変更前、変更後
- 引数 / フィールド、型・形式、必須 / 任意、既定値、null / omitted / emptyの区別
- request / input、response / output、エラー・status・exit code、認証認可
- 順序、retry、互換性、migration、rollback / recoveryのうち該当するもの
- 代表的な正常例と境界 / 失敗例
- 対応する`D<n>`と`AC<n>`、派生artifact / 同期先、残る仮定またはopen decision

該当しない契約要素は列挙せず、外部挙動が変わらない重要な要素は「変更なし」と明示します。
特にAPI / CLI / DB schema / 公開型 / 出力形式は、要約表の1セルに圧縮せず、カード内で入出力、
失敗、互換性の全貌を判断できる粒度で示します。

**状態はsurface familyごとに持ちます。** 各familyは`draft` / `presented` / `agreed`の
いずれかで、ゼロ件宣言は1個のfamilyと同じ扱いにします。全familyが`agreed`の時だけ
外部サーフェス全体が`agreed`です。`draft`は作成直後または内容が変わった直後、
`presented`は判断可能な契約カードを提示してユーザーの応答を待っている状態、`agreed`は
ユーザーがそのfamilyへ合意した状態を指します。

**唯一の停止条件**: 仕様相当artifactを持つworkflowでは、`spec 承認の要求`・
`実行方法の選択の提示`・次phaseへの`handoff`・
`session をまたぐ中断（compact を含む）`のいずれよりも前に、最新の外部サーフェスが
`agreed`でなければなりません。この停止条件は、最初の未完了gateから続ける再開経路にも
同様に適用します。agreed でなければそれらへは進みません。**唯一の例外は保留**
（後述の終了状態）で、ユーザーが保留を選んだ場合に限り、未合意のまま停止してよい
です（`session をまたぐ中断`と、同じphaseを再開するための状態保存・session間の
引き継ぎを含みます）。保留でも、spec承認の要求・実行方法の選択の提示・次phaseへの
handoffは行いません。再開時は`progress.md`から状態を復元し、未合意familyを再提示
します。**意図しない中断（自動compactを含む）からの再開は保留と同じ扱いとし**、
`progress.md`の状態を復元して未合意familyを再提示してから先へ進みます。

内容が変わったfamilyとそのdependency coneだけを`draft`へ戻し、無関係なfamilyの合意は
保持します。判定できない候補familyだけを`draft`に倒し、revision、変更family、dependency cone、
理由を`progress.md`へ記録します。

提示と合意は次のように行います。

1. 一覧と全契約カードを同じ1回の提示に載せ、各familyを`presented`にします。ユーザーが
   他のartifactを開かなくても判断できることを提示前に確認します。
2. 「全部承認」「そのままで」など、外部サーフェスに対する**明示的一括承認**は、
   後述の個別合意必須familyを除くすべての`presented` familyを`agreed`にします。
3. 一部のfamilyだけに変更指示がある場合、`他は承認`などの明示があるときだけ、言及されなかった
   個別合意不要の`presented` familyを`agreed`にします。明示がなければ`presented`を維持します。
   変更対象とそのdependency coneだけを`draft`へ戻します。
4. security/認証認可、課金、破壊的migration、データ損失、不可逆操作、または未解決の
   product decisionを持つfamilyは`個別合意必須`と明記し、一括承認の対象にしません。
   通常の公開API変更や後方互換性だけを理由に個別合意必須にしません。
5. 個別合意必須familyだけは番号順に1件ずつ確認します。その他のfamilyを理由なく
   一問一答にしません。
6. 外部サーフェスに言及しない応答（spec承認だけ / 実行方法だけ）は合意とみなさず、
   未合意familyを名指しで再提示します。
7. 再提示では一覧全体と`draft` familyの契約カードを示し、`agreed` familyは状態を変えず
   参照用に要約します。
8. `progress.md`に一括提示 / 一括承認 / 個別合意 / 変更指示 / 保留 / 中止を記録します。

終了状態は**保留**（未解決の内容と最新revisionを`progress.md`に残して停止でき、再開時に
必ず再提示）と**中止**（workflow終了）の2つで、合意しないまま先へ進む終了状態はありません。

`## 外部サーフェス`節を作成・変更したら、提示前にfamily分割、契約カードの判断可能性、
本文との整合、派生artifactのグループ化、個別合意必須の判定を検査します。通常経路は
Completeness reviewer、短縮経路はcontrollerが検査します。既存review後に変更した場合は、
`### 変更後のclosure review`に従って変更familyとdependency coneだけを確認します。

`## 外部サーフェス`節を書き終えた時点で、既存のprotected contract判定に照らして
短縮経路成立性を再評価します。順序は`節の作成 → 検査 → 短縮経路成立性の再評価 →
成立時だけ提示`です。

適用外と移行は次によります。仕様相当artifactを作らない場合（調査のみで停止、
全ステップを通さない軽微な変更）は適用しません。本規定の投入前に作られた
artifactを持つworkflowは、仕様承認済みかを問わず、**上記の停止条件のいずれよりも
前に**節を起こし、検査・提示・合意を行います。

## 短縮経路

controllerは、request、外部挙動、acceptance criteria、validationが明確で、変更が局所的
（file数だけでは判定しない）、protected contract・migration・architecture decision・複雑な
concurrency/distributionを含まず、既存の未commit変更を安全に分離できるという全条件を
満たす場合だけ、通常のdiscovery/spec/planを省略できます。

short-pathの遷移は`SHORT_TASK_DRAFT -> SHORT_TASK_PREFLIGHT -> EXECUTION_CHOICE`です。
唯一のtask artifactとして`.aidocs/workflows/<workflow-id>/tasks/01-short-path.md`を
作成します。Goal、Non-goals、acceptance criteria、owned paths、test target、期待する
RED reason（非挙動変更では理由と代替検証）、validation command、stop
conditions、ユーザーのexecution choiceを含めます。acceptance criteriaには`AC1`から
連番を振ります。short pathでは`spec.md`がAC識別子を持たないため、`tasks/01-short-path.md`
が**regular fileとして**存在しかつ`spec.md`がL1を満たさない場合にlintのL1（spec.mdのAC識別子検査）が全edgeで
免除されます（`spec.md`自体はhelperが空fileとして必ず作るので、不在では判定しません）。
L2（final reviewのAC判定検査）は課されたままで、そのAC IDの出所は`spec.md`ではなく
この`tasks/01-short-path.md`になります。どちらのexecution
choiceも提示する前にControllerがclarity、scope、decision、owned paths、test/RED、
validation、非挙動変更の理由を確認し、canonical risk matrixが要求する場合だけfresh reviewを行います。
normative gapまたは重要なpreflight Findingがあればshort pathを取り消し、discoveryへ
戻るか、task artifactを修正して再reviewします。

## artifactと引き継ぎの不変条件

workflow artifact配下に`spec.md`と`plan.md`を書き、reviewer reportを`reviews/`に保持し、
監査証拠を`progress.md`へ追記します。controllerのpacketには絶対artifact path、固定
scope、reviewer role/model、validation command、stop conditionを記載し、長いdiffは
貼り付けません。各引き継ぎでartifact revisionと`context.json`のphaseを検証します。
欠落、stale、矛盾、またはstateより先行した証拠はstop conditionです。

### 既存の実行依頼

実行方法の二択は未選択の場合だけ提示する。レビュー済み成果物の scope 内の実装を既に明示依頼されていれば、その依頼を根拠に `execute-plan` を記録して続ける。commit / push / MR まで明示依頼されている場合だけ `execute-and-ship` と shipping 認可を記録する。plan のみの依頼では停止する。spec の明示承認、外部サーフェス合意、sanitize、cleanup の gate はこの規則で省略しない。
