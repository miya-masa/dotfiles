# spec と plan の契約

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

質問は依存が解けた順に**1 ターン 1 問**（`AskUserQuestion`）。2〜3 案と推奨、trade-off を添える。回答を記録し、下流の依存を再評価する。**コード / test / docs / schema / public interface から分かる事実をユーザーに尋ねない**（探索は explorer に委譲するか controller が読む）。

### spec review

draft が揃ったら、結論を互いに共有しない fresh reviewer を独立に起動する。既定レンズは Completeness / Soundness / Operability / Simplicity で、protected contract / security / migration / 並行・分散状態に触れる時だけ Adversarial（Risk）を追加する。該当しないレンズは省き、常時多並列にしない（発動条件は `review-common.md` のリスク表に従う）。レンズ定義は `review-lenses.md`、起動 model は [roles.md](roles.md) に従う。

各 reviewer は根拠・impact・最小の修正または検証方法・verdict を返す。controller は全 finding を `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類して `reviews/` に記録する。黙って結論をマージしない。採用分を反映したら、影響した review scope だけ再実行する。normative な gap は discovery へ戻す。

**review 反映済み spec をユーザーが明示承認するまで planning へ handoff しない。** 承認は `progress.md` と `context.json` に記録する。

## planning packet と plan

planning の入力は**明示承認済みの spec とその evidence だけ**。controller が plan を書き、fresh reviewer が反証する。plan は implementer が追加判断なく実行できる **decision-complete** な状態にし、product や architecture を作り直さない。

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

task 内部の action は 2〜5 分単位の固有手順（test 対象、期待する RED 理由、command、最小実装の境界）にする。production code を丸ごと貼らない。共通の RED/GREEN/refactor 手順を各 task に複製しない。

### plan review と実行方法の二択

完成した plan を fresh reviewer 1 体に渡し、spec coverage / scope / decision completeness / 依存 / interface / 検証可能性**だけ**を見させる（architecture の再設計はさせない）。finding は採用 / 却下 / 要ユーザー判断で記録する。normative な spec gap は plan で回避せず `product-discovery` へ戻す。protected contract、architecture、権限、永続化、分散状態の未決は停止する。

review 通過後は**実装を開始せず**、次の二択をユーザーに提示して停止する。

- `execute-plan`: task 実行・review・local verification まで行い、そこで止まる。
- `execute-and-ship`: 同じことをした上で、別途認可された commit / push / MR / in-scope CI まで続ける。

この選択が増やすのは **shipping 権限だけ**で、承認済み scope は広がらないことを説明する。選択を `context.json` に記録するまで実装を始めない。

## short path

次の条件が**すべて**成り立つ時だけ、通常の discovery / spec / plan を省略できる。

- 要求、外部挙動、acceptance criteria、validation が明確
- 実装時に残る設計判断が無い（**ファイル数では判断しない**）
- protected contract、migration、architecture 判断、複雑な並行 / 分散処理を含まない
- 既存の未コミット変更を安全に分離できる

遷移は `SHORT_TASK_DRAFT → EXECUTION_CHOICE`。`tasks/01-short-path.md` を唯一の task artifact として作り、Goal / Non-goals / acceptance criteria / owned paths / test 対象 / 期待する RED 理由（または承認済みの TDD 例外）/ validation command / stop conditions / ユーザーの実行方法選択を書く。

**preflight review は挟まない。** controller が上の条件と task artifact の決定完了度を自分で確認し、満たさないと判断したら short path を取り消して discovery へ戻す。差分全体の敵対的検証は `execute-plan` の final review が担う。**short path でも実行方法のユーザー選択を省略しない。**

## mid-flow entry（既に spec がある場合）

Story = 確定した 1 タスクとして spec 相当が既にある場合は、discovery 対話を省いて **spec review gate から開始**する。既存 spec を `spec.md` として artifact に取り込み、fresh review → 明示承認 → `implementation-planning` の順は変えない。`implementation-planning` へ直接入る経路は作らない（承認済み spec だけを planning の入力にする不変条件を守るため）。

## artifact と handoff の不変条件

`spec.md` と `plan.md` を workflow artifact 配下に書き、reviewer の報告を `reviews/` に残し、監査 evidence を `progress.md` に append する。controller の packet には artifact の絶対 path、固定した scope、reviewer の役割と model、validation command、stop conditions を書き、長い diff を貼らない。handoff のたびに artifact revision と `context.json` の phase を検証する。欠落・stale・矛盾・state より先行した evidence は stop condition。
