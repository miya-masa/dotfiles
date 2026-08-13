# レビューレンズ

spec / plan / 診断 brief / コード差分をレビューする時に使うレンズの定義。共通制約（発動条件 / 敵対的検証の原則 / Finding gate / 採用判定）は [review-common.md](review-common.md)、エッジケースの洗い出し手法は [analysis-techniques.md](analysis-techniques.md) にある。

どのレンズをどの model・effort で起動するかは runtime 依存なので、ここには書かない（Claude Code は `~/.claude/skills/product-discovery/references/roles.md`、Codex は `~/.codex/review-policy.md`）。

該当しないレンズは省く。常時多並列にしない。レンズを分ける時は、各 reviewer に他のレンズの結論や指摘を渡さない。

## 設計レンズ（spec / plan）

| レンズ | 観点 | 起動条件 |
|---|---|---|
| Completeness | 決定表、状態遷移、境界、エラー、互換性、AC。未定義動作を探す | 基本 |
| Soundness | 不変条件、依存、時間軸。論理破綻と race を探す | 基本 |
| Operability | 互換性、移行、rollback、観測性、test の検証可能性 | 基本 |
| Simplicity | scope creep、不要な要件・抽象化。要求されていないものが入っていないか | 基本 |
| Adversarial / Risk | 敵対的検証の専任。spec の中心的主張・前提・採用判断を「間違っている前提」で反証し、反例を一次情報に接地して示す。信頼境界に触れる spec では攻撃者視点でバイパスと悪用も探す | protected contract、security、migration、並行・分散状態、または根拠の薄い中心的主張がある時 |

plan に適用する時は、対象を「spec の各要件に対応する task があるか / decision-complete か / 分割と順序 / 検証手段 / 中断耐性」に読み替える（plan 固有の観点は `spec-and-plan.md` 側の plan 契約にある）。

依頼例:

> 対象 spec `<path>` を Completeness レンズだけで fresh review してください。`analysis-techniques.md` の決定表、状態遷移、境界を使い、未定義動作を探してください。共通制約に従い、各 Gap に v1 必要性（`v1 必須 / v1.x で可 / 将来拡張で十分`）を付けてください。

> 対象 spec `<path>` を Adversarial レンズだけで fresh review してください。この spec は間違っているという前提で、中心的主張・前提・採用判断への反証を試み、反例を spec 本文と一次情報に接地して示してください。信頼境界に触れる場合は `analysis-techniques.md` の攻撃者視点でバイパスと悪用も探してください。共通制約に従って報告してください。

## 実装後レンズ（コード差分）

| レンズ | 観点 | 起動条件 |
|---|---|---|
| Correctness | spec 適合、ロジック、過不足、回帰 | 基本 |
| Robustness | 並行処理、状態遷移、resource、Close/Shutdown、retry、冪等性 | 基本 |
| Simplicity | reuse、重複、効率、不要な抽象化の削減。正しさのレンズと混同しない | 基本 |
| Security | 攻撃者視点。認証認可バイパス、fail-open、正規操作の組み合わせ悪用、入力、secret、信頼境界 | 該当時 |
| Contract | public API、DB schema、後方互換、caller 影響 | 該当時 |
| Holistic（統合） | レンズ横断の反証専任。spec と実装全体の整合、モジュール間・関心事間の相互作用、個別レンズの定義の隙間に落ちる欠陥。Security 観点は扱わない | レンズ並列時は既定 1 本。他レンズと並行起動可・他レンズの指摘は渡さない |

言語や専門領域の skill（`reviewing-golang` / `database-review` 等）は reviewer 起動時に装着する。修正は実装役に委譲し、reviewer は read-only で変更しない。

依頼例:

> `git diff` を Robustness レンズだけで fresh review してください。並行処理、状態遷移、resource lifecycle、失敗時挙動、retry、冪等性を確認し、共通制約に従って報告してください。read-only で変更しないでください。

> `git diff` を Security レンズだけで fresh review してください。`analysis-techniques.md` の攻撃者視点を実装に適用し、認証認可のバイパス経路、エラー時の fail-open、正規操作の組み合わせによる悪用を実際の実行経路で探してください。共通制約に従って報告し、read-only で変更しないでください。

Holistic は上位モデル向けに手順を列挙せず、ゴールと制約だけ渡す:

> `git diff` と spec `<path>` を対象に、この実装は間違っているという前提で反証を試みてください。個別観点（正しさ・堅牢性・security・契約）の定義に収まる指摘より、spec と実装全体の整合、モジュール間・関心事間の相互作用など、観点の隙間に落ちる欠陥を優先してください。security 観点は扱わないでください。共通制約に従って報告し、read-only で変更しないでください。

## task レンズ（1 task 単位）

plan の 1 task を実装した直後に、その task packet と evidence だけを対象に使う。差分全体のレビューではないので、実装後レンズの代わりに次の 2 verdict を**別々に**返す。

| verdict | 観点 |
|---|---|
| Spec compliance | task の goal / AC / owned paths / 検証結果に対する適合。過不足と、owned paths 外への波及 |
| Simplicity | 最小差分か。不要な抽象化、将来拡張、過剰な defensive coding が入っていないか |

2 つを 1 つの結論へ混ぜない。ファイルを変更せず、信頼済みの command を再実行しない。

## 診断レンズ（診断 brief）

| 観点 |
|---|
| root cause が再現と evidence を過不足なく説明するか（相関を因果と取り違えていないか） |
| 対立仮説を証拠で棄却できているか |
| Impact scope の限定が適切か |
| 証拠の穴を防御的な guard で埋めていないか |

protected contract・データ損失・不可逆処理が絡む、または仮説が競合したまま残る場合は fresh reviewer に反証役として委譲する。
