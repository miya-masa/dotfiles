# spec と plan の契約

discovery 担当は spec（short path は task）に `| AC ID | Lifecycle | Criterion |` の canonical table を1つ作る。Controller は plan 確定後（short path は task 確定後）に `evidence.json` を登録し、final review 前に source と registry を照合する。review 後の binding、local verification の collector、各 gate の担当・時点・schema は共有 `~/.agents/workflows/software_delivery/references/evidence-contract.md` の phase 手順に従う。

この契約は artifact を初期化した正式 workflow に適用する。明確な局所変更は初期化前に共通 effort-policy.md の直接完了条件で扱う。既存 workflow / active AC を途中から直接経路へ落とさず、承認・外部サーフェス・snapshot・shipping gate を保持する。


`product-discovery` と `implementation-planning` が共有する契約。引き継ぎの実体は workflow artifact `.aidocs/workflows/<workflow-id>/` で、`context.json` が唯一の機械可読な state authority。`spec.md` / `plan.md` / `reviews/` / `tasks/` / `progress.md` は evidence であって、**報告だけで phase を進めない**。

- state と helper CLI: `~/.claude/skills/execute-plan/references/state-and-artifacts.md`
- reviewer / implementer の起動体制と packet: [roles.md](roles.md)
- レンズ定義: `~/.agents/workflows/software_delivery/references/review-lenses.md`
- レビュー共通制約: `~/.agents/workflows/software_delivery/references/review-common.md`
- 分析手法: `~/.agents/workflows/software_delivery/references/analysis-techniques.md`

## discovery packet と spec

controller は依頼、repository の一次証拠、現在の挙動、ユーザーの決定、仮定、未知を evidence packet に記録する。spec は**事実 / 推論 / 仮定 / 未決を分離**し、次を含める。

- Goal と利用者、Context、Constraints、scope と Non-goals
- 外部から観測できる normative な挙動、主要フロー、状態 / エラー / 権限 / 境界の規則、互換性と protected contract の制約
- Given/When/Then の acceptance criteria、検証 evidence、仮定
- scope 内の結果を変えうる未決事項が残っていないこと

**acceptance criteria は `AC1` から、設計判断は `D1` から連番を振る**（設計判断にはそう決めた理由を 1 行添える）。番号は下流の plan / task / test / review が同じ項目を名指しするための識別子で、`execute-plan` の final review が要求する AC 判定表もこの番号に依存する。**番号のない条件は、後から「どこで分かれたか」を特定できない。**

`spec.md` に AC 識別子を含む行があることは `SPEC_REVIEWS → USER_APPROVED_SPEC` で機械検査される（L1、`~/.claude/skills/execute-plan/references/state-and-artifacts.md` 参照）。無ければ `transition` が `artifact lint failed` で rc=1 になり `context.json` は変わらない。

結果を変える判断だけを質問し、依存する問いは順に、独立した問いは推奨案と trade-off を添えてまとめる。回答を記録し、下流の依存を再評価する。**コード / test / docs / schema / public interface から分かる事実をユーザーに尋ねない**（探索は explorer に委譲するか controller が読む）。

### spec review

draft が揃ったら、結論を互いに共有しない fresh reviewer を独立に起動する。既定レンズは Completeness / Soundness / Operability / Simplicity で、protected contract / security / migration / 並行・分散状態に触れる時だけ Adversarial（Risk）を追加する。該当しないレンズは省き、常時多並列にしない（発動条件は `review-common.md` のリスク表に従う）。レンズ定義は `review-lenses.md`、起動 model は [roles.md](roles.md) に従う。

各 reviewer は根拠・impact・最小の修正または検証方法・verdict を返す。controller は全 finding を `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類して `reviews/` に記録する。黙って結論をマージしない。採用分を反映したら、影響した review scope だけ再実行する。normative な gap は discovery へ戻す。

**review 反映済み spec をユーザーが明示承認するまで planning へ handoff しない。** 承認は `progress.md` と `context.json` に記録する。

## planning packet と plan

planning の入力は**明示承認済みの spec とその evidence だけ**。通常は `deliberator`（`task_kind=planning`）が計画を検討し、controller が根拠を検査してartifactへ統合する。既存決定の機械的な転記だけなら直接行い、必要なfresh reviewerが反証する。plan は implementer が追加判断なく実行できる **decision-complete** な状態にし、product や architecture を作り直さない。

独立に検証できる vertical slice へ分解し、各 task に次の 9 項目を持たせる。

| field | 要件 |
|---|---|
| goal | 観測可能な結果 1 つ |
| owned paths | implementer が変更してよい正確なファイル / ディレクトリ |
| deliverables | コード / docs / test、または機械的な出力 |
| dependencies | 先行 task、evidence、順序 |
| interfaces | 入出力、シンボル、外部境界 |
| acceptance criteria | 客観的な Given/When/Then か同等のもの |
| validation | 正確な command と期待結果 |
| RED 理由 | 実装前に focused test が失敗するべき理由 |
| stop conditions | 競合、protected contract、scope、信頼できない validation |

task 内部は所要時間で刻まず、test 対象、期待結果、command、最小実装の境界を示す。production code を丸ごと貼らない。共通の RED/GREEN/refactor 手順を各 task に複製しない。

### plan review と実行方法の二択

implementation-planning の skip 条件を満たさない plan だけを fresh reviewer 1 体に渡し、spec coverage / scope / decision completeness / 依存 / interface / 検証可能性**だけ**を見させる（architecture の再設計はさせない）。finding は採用 / 却下 / 要ユーザー判断で記録する。normative な spec gap は plan で回避せず `product-discovery` へ戻す。protected contract、architecture、権限、永続化、分散状態の未決は停止する。

review 通過後は「既存の実行依頼」に従う。未選択時だけ次の二択を提示し、実行依頼がなければ計画で停止する。

- `execute-plan`: task 実行・review・local verification まで行い、そこで止まる。
- `execute-and-ship`: 同じことをした上で、別途認可された commit / push / MR / in-scope CI まで続ける。

この選択が増やすのは **shipping 権限だけ**で、承認済み scope は広がらないことを説明する。選択を `context.json` に記録するまで実装を始めない。

## 外部サーフェス合意

`product-discovery` が spec 相当 artifact（通常経路と mid-flow entry は `spec.md`、short path は `tasks/01-short-path.md`）を書くときは、必ず `## 外部サーフェス` 節を持たせる。本体は次の 5 列の表、または「外部サーフェスの新設・変更・廃止なし」の 1 行（ゼロ件宣言）のいずれかにする。

| # | 項目 | 区分 | 決めた内容 | 根拠 |
|---|---|---|---|---|
| 表の先頭からの連番（1 始まり）。ユーザーが番号で指せるようにするための識別子 | サーフェスの識別名（endpoint、フラグ名、設定キー、環境変数名、型名、テーブル/カラム名、ファイル名など） | 新設 / 変更 / 廃止（変更・廃止は変更前の値も書く） | 名前と、契約要素の正準集合（下記）のうち該当するもの | そう決めた理由 1 行 |

`#` は**提示のたびに先頭から振り直す**（安定 ID は作らない）。変更指示は直前に提示した番号を指すものとして解釈し、行の増減で番号が変わった場合は再提示時にその旨を 1 行添える。

行にするかどうかの判定基準は次の 2 つで、種別の分類ではない。

1. この変更で新しく増える・変わる・無くなる、ユーザーまたは他コンポーネントが名前で参照するもの。
2. 名前が変わらなくても、外部から観測できる挙動・失敗・互換性の契約が変わるもの。

代表例（閉じた集合ではない）: API / CLI のシグネチャ、設定キーと既定値、環境変数、出力・ファイル形式、DB schema、公開型、ファイル配置とパス、キーバインド、エージェント自身の停止条件やユーザーへの提示形式。**基準を満たすか判断できない項目は載せる側に倒す。**

**状態は表の行（項目）ごとに持つ。** 各行は `draft` / `presented` / `agreed` のいずれかで、ゼロ件宣言は 1 個の行と同じ扱いにする。外部サーフェス全体が `agreed` なのは、**全行が `agreed` の時だけ**。`draft` は作成直後または内容が変わった直後、`presented` は compact view または 2 段目の個別提示を行いユーザーの応答を待っている状態、`agreed` はユーザーが全行またはゼロ件宣言に合意した状態を指す。

**唯一の停止条件**: spec 相当 artifact を持つ workflow では、`spec 承認の要求・実行方法の選択の提示・次 phase への handoff・session をまたぐ中断（compact を含む）`のいずれよりも前に、最新の外部サーフェスが `agreed` でなければならない。`agreed` でなければそれらを行わない。**唯一の例外は保留**（後述の終了状態）で、ユーザーが保留を選んだ場合に限り、未合意のまま停止してよい（`session をまたぐ中断`と、同じ phase を再開するための状態保存・session 間の引き継ぎを含む）。保留でも、spec 承認の要求・実行方法の選択の提示・次 phase への handoff は行わない。再開時は `progress.md` から状態を復元し、未合意行を再提示する。**意図しない中断（自動 compact を含む）からの再開は保留と同じ扱いとし**、`progress.md` の状態を復元して未合意行を再提示してから先へ進む。

**内容が変われば原因を問わず `draft` へ戻り、それまでの合意は失効する。** ユーザー指示による変更、reviewer finding の反映、本文修正の波及のいずれも同じ扱いとする。**失効の範囲は、内容が変わった行と、その変更が波及した行だけ。** 波及の有無は controller が判定し、提示前検査（後述）の結果を入力にする。判定できない候補行は `draft` に倒す。変更行と波及候補行は revision とともに `progress.md` へ記録する。無関係な行の合意は保持する。

提示と応答は 2 段構えにする。

1. **1 段目（全行の一括提示）**: compact view（`#` / `項目` / `区分` / `決めた内容` の 4 列。`根拠` 列は省く）を番号付きで全行提示し、「変更したい項目は番号で指摘してほしい」と、これから 1 件ずつ詰める行の番号を添える。ゼロ件なら定型 1 行を提示し、これも 1 個の合意対象として扱う。
2. **契約要素の正準集合**（9 要素）: 引数 / フィールド、型・形式、既定値、必須 / 任意、認証要否、エラー・status・exit code、順序、retry、互換性。「名前」は全行に必ず書かれるので数に含めない。複合表記（例「エラー・status・exit code」）は列挙単位で 1 要素と数える。この集合は上表の「決めた内容」列と共通で、他はここを参照する（再列挙しない）。
3. **2 段目（詳細合意が要る行の一問一答）**: 該当行を番号順に 1 件ずつ提示し、行ごとに合意を取る。提示ではその行の名前と該当する契約要素を省略せず書き、表の 1 セルへ圧縮しない。1 件ごとに合意 / 変更指示を `progress.md` へ残す。
4. **詳細合意が要る行の判定基準**: 決定する契約要素が 2 つ以上ある行。実際にセルへ書いた語数ではなく決定する要素数で数え、controller が表の作成時に数え、提示前検査の担い手が提示前に確認する。代表例は API / CLI のシグネチャ、設定キーと環境変数、DB schema、公開型、出力・ファイル形式。判断できない行は詰める側に倒す。残りの行は 1 段目の一括合意で済ませてよい。
5. 外部サーフェスの全行が `agreed` になるまで、compact view と 2 段目の提示だけを単独で出して応答を待つ（spec 本文・plan・実行方法を同じ提示に載せない）。全行 `agreed` になった後なら、spec 承認と plan と実行方法を 1 回にまとめてよい。
6. 一部の行にだけ変更指示を返した応答は、言及されなかった詳細合意不要行への一括合意として扱う（詳細合意が要る行には及ばない）。一括合意（「全部 OK」「そのままで」）も同様に詳細合意不要行への合意に留まる。**外部サーフェスに言及しない応答（spec 承認だけ / 実行方法だけ）は合意とみなさず、未合意として名指しで再提示する。**
7. 変更指示を受けたら artifact の表と本文へ反映し、節と本文全体の整合を確認する（専門レンズの再 review は影響 scope に絞ってよい）。反映後は `draft` へ戻るので最新 compact view を再提示する。再提示は全行を出すが、状態遷移の対象は `draft` の行だけで、`agreed` の行は状態を変えずに参照用として並べる。2 段目は未合意の詳細行だけを最新の番号順で処理する。
8. `progress.md` に提示 / 合意 / 変更指示 / 保留 / 中止を 1 行ずつ残す。
9. 終了状態は**保留**（未解決の内容と最新 revision を `progress.md` に残して停止してよい。上記の例外に従い、再開時に必ず再提示する）と**中止**（workflow 終了）の 2 つで、合意しないまま先へ進む終了状態は無い。

`## 外部サーフェス` 節を作成・変更したら、compact view を提示する前に節と本文の整合を検査する。通常経路と mid-flow entry は spec review gate の Completeness reviewer が検査し、short path は controller 自身が検査する（short path で新たな reviewer を起動しない）。既存の review が完了済みでも、その後に節を後付け・変更したらこの検査をやり直す。この検査は、上記の詳細合意が要る行の判定が正しく行われているかの確認も兼ねる。

`## 外部サーフェス` 節を書き終えた時点で、既存の protected contract 判定に照らして short path 成立性を再評価する。順序は `節の作成 → 検査 → short path 成立性の再評価 → 成立時だけ提示`。

適用外と移行は次による。spec 相当 artifact を作らない場合（調査のみで停止、全ステップを通さない軽微な変更）は適用しない。本規定の投入前に作られた artifact を持つ workflow は、spec 承認済みかを問わず、**上記の停止条件のいずれよりも前に**節を起こし、検査・提示・合意を行う。

## short path

次の条件が**すべて**成り立つ時だけ、通常の discovery / spec / plan を省略できる。

- 要求、外部挙動、acceptance criteria、validation が明確
- 実装時に残る設計判断が無い（**ファイル数では判断しない**）
- protected contract、migration、architecture 判断、複雑な並行 / 分散処理を含まない
- 既存の未コミット変更を安全に分離できる

遷移は `SHORT_TASK_DRAFT → EXECUTION_CHOICE`。`tasks/01-short-path.md` を唯一の task artifact として作り、Goal / Non-goals / acceptance criteria / owned paths / test 対象 / 期待する RED 理由（非挙動変更では理由と代替 validation）/ validation command / stop conditions / ユーザーの実行方法選択を書く。**acceptance criteria には `AC1` から連番を振る**（short path では L1 が免除される代わりに、final review が要求する AC 判定表がこの番号を名指しする）。

**preflight review は挟まない。** controller が上の条件と task artifact の決定完了度を自分で確認し、満たさないと判断したら short path を取り消して discovery へ戻す。差分全体の敵対的検証は `execute-plan` の final review が担う。**short path でも実行選択の記録を省略しない。「既存の実行依頼」に従い、同じ許可を聞き直さない。** `tasks/01-short-path.md` にも `## 外部サーフェス` 節を必須で持たせ、書き終えた時点で「外部サーフェス合意」の手順に従って short path 成立性を再評価する。

## mid-flow entry（既に spec がある場合）

Story = 確定した 1 タスクとして spec 相当が既にある場合は、discovery 対話を省いて **spec review gate から開始**する。既存 spec を `spec.md` として artifact に取り込み、fresh review → 明示承認 → `implementation-planning` の順は変えない。`implementation-planning` へ直接入る経路は作らない（承認済み spec だけを planning の入力にする不変条件を守るため）。

## artifact と handoff の不変条件

`spec.md` と `plan.md` を workflow artifact 配下に書き、reviewer の報告を `reviews/` に残し、監査 evidence を `progress.md` に append する。controller の packet には artifact の絶対 path、固定した scope、reviewer の役割と model、validation command、stop conditions を書き、長い diff を貼らない。handoff のたびに artifact revision と `context.json` の phase を検証する。欠落・stale・矛盾・state より先行した evidence は stop condition。

### 既存の実行依頼

実行方法の二択は未選択の場合だけ提示する。レビュー済み成果物の scope 内の実装を既に明示依頼されていれば、その依頼を根拠に `execute-plan` を記録して続ける。commit / push / MR まで明示依頼されている場合だけ `execute-and-ship` と shipping 認可を記録する。plan のみの依頼では停止する。spec の明示承認、外部サーフェス合意、sanitize、cleanup の gate はこの規則で省略しない。
