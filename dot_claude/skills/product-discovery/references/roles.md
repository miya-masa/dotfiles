# role と委譲の規律（Claude Code）

workflow の各 role を Claude Code の subagent へ対応付ける表と、起動時の規律。レビューの観点定義そのものは `~/.agents/workflows/software_delivery/references/review-lenses.md`、共通制約は同 `review-common.md` にある。

## role 対応と起動設定

通常model/effortと昇格基準は `~/.agents/workflows/software_delivery/references/effort-policy.md` が正本。Controllerは要件・state・dispatch・結果を統合し、通常の仕様/計画は `deliberator`、実装は `implementer`、独立reviewは `reviewer` へ渡す。既存決定の転記や委譲より短い明確な小変更だけ直接処理する。

- `deliberator` の packet は `task_kind=specification|planning|debugging` のいずれか1つを指定する。各phaseの範囲だけを扱い、artifact/stateの書き込みとユーザー合意はControllerが行う。specとplanが既に十分なら再作成しない。
- 実装中の計画不足は `deliberator` へ戻す。計画が十分でも実装固有の推論が難しい場合だけ `implementer-high` を選ぶ。高いmodelで未決のproduct/architecture判断を代行させない。
- 限定探索は `explorer`、独立した実入口検証が必要なら `verifier`（sonnet / low）。クロスモデル確認は明示依頼時だけ末尾のherdr契約を使う。

reviewの人数・lens・適用条件は共有 `review-common.md` だけを正本とする。同一scope/snapshotにtask reviewとfinal reviewを重ねない。

### runtimeとfailure route

Agent toolはnative profileのmodel/effortを使う。model overrideだけではfrontmatterのeffortを変えられないため、highが必要なら `deliberator` / `implementer-high` / `reviewer` を選ぶ。未確認のper-call effort引数や、新CLI sessionの `--agents` を通常のdispatchとして扱わない。model allowlist・環境変数等が上書きする場合は実効設定を確認し、指定値と実効値を区別してagent ID/statusと選択理由を記録する。観測できない実効値は未確認とし、必須条件が満たせなければ停止する。

optionalな探索・実装・verifierが起動できない時は条件を再確認してControllerが直接続けられる。必須の判断・独立review・診断がunavailable、証拠不足、矛盾なら停止または問いを絞って再起動し、低いmodel/effortへ黙って代替しない。

## subagent packet

Agent tool の prompt は**それ自体で完結**させる。セッション履歴を継承しない前提で、次を書き込む。

1. ユーザーの目的
2. 具体的な問い（またはこの起動で達成すること）
3. 対象範囲（絶対 path）
4. 既知の事実（一次証拠の所在）
5. 現在の仮定
6. 制約と non-goal
7. 決定済み事項
8. 未解決事項
9. ファイル変更の可否
10. 必要な成果物の形
11. 完了条件
12. 固定した絶対 workdir（worktree を使う場合）

### 起動時の規律

- named agent の frontmatter にある model / effort を使い、共通policyの例外だけ明示指定する。未対応の override を仮定しない。
- **dispatch prompt にセッション履歴や前 task のサマリを貼らない。** 渡すのは task・触る interface・global constraints だけで、成果物はファイル path で受け渡す。長い貼り付けは packet の実質を薄める。
- 自分の作業の再確認のために subagent を起動しない。起動理由は workflow 上の role 分離（fresh context による確証バイアス対策）か、広く探す必要がある調査に限る。
- 1 体で足りる仕事に複数体を割かない。
- 指示文を書くコストが作業そのものと同等なら、委譲せず controller が直接やる。
- MCP を使う操作は controller が直接行う（subagent は親セッションの MCP 接続を継承しない）。
- 言語 / 専門 skill（`coding-golang` / `testing-golang` / `reviewing-golang` / `database-review` 等）は起動時に controller が装着する。

## 並列委譲

独立した問題ドメインが 2 つ以上ある時だけ並列にする。`execute-plan` の task 実行は**直列**で、ここでの並列は別の場面（独立した複数調査、レンズ並列レビュー、無関係な複数テスト失敗）を指す。

- 並列にしてよい条件: 各ドメインが独立して理解でき、共有状態がなく、順序依存がない。
- 直列にするもの: 関連する失敗（1 つ直すと他も直るかもしれないもの）、全体状態の把握が要る調査、同じファイルを触る実装。
- 1 応答に複数の Agent 呼び出しを並べると並列実行、1 応答 1 呼び出しは直列。
- 各 agent に渡すのは「1 ドメインに絞った scope / 明確なゴール / 変更してはいけない範囲 / 返してほしい成果物の形」。
- 返ってきたら要約を読み、変更が衝突していないか確認し、影響する interface の検証を通してから統合する。

## 採用判定

reviewer は severity で足切りしない設計なので、絞り込みは controller の採用判定が本番。全指摘を一次情報（spec 本文 / diff / コード / 実行結果）で裏取りし、`今回修正 / 見送り（根拠付き）/ 要判断` に分類する。裏取りせずに採用も却下もしない。diff 全体を controller が読み直すことはせず、指摘箇所をスポットで読む。

approve 基準と gate 通過条件は `~/.agents/workflows/software_delivery/references/review-common.md` の採用判定に従う。

`/code-review` はトークン固定費が重いため自動発火させず、ユーザーが明示起動した時だけ使う。`codex-doublecheck`（ユーザー明示指示による 1 周のクロスモデル確認 wrapper）も既定フローに含めない。クロスモデル確認を明示依頼された時だけ `herdr-delegate` を利用する。端末環境の存在は追加 review の理由にしない。

## herdr 内クロスモデル並走（spec review gate / final review）

クロスモデル確認の明示依頼があり、`HERDR_ENV=1` かつ `~/.claude/data/harness/cross-model-off` が存在しない かつ `command -v codex` が成立する時、`product-discovery` の spec review gate と `execute-plan` の final review は、必要な reviewer と同時に Codex（`herdr-delegate` の `agent` モード）を起動する。判定はこれら呼び出し元 skill が行い、共有契約 `herdr-delegate` は関知しない。**review gate の数は増えない**（既存の 2 つの gate に Codex が相乗りするだけ）。

- Codex への入力は spec review では spec 全文、final review では diff + spec + plan のみ（0-context、scratch 隔離で機構的に担保）。前周の finding や Claude 側の結論は渡さない。
- 両者の結論は互いに共有しない。
- 突き合わせは finding 単位。Claude 側は複数レンズが各自の領分を見るのに対し Codex は全観点を 1 体で見るため、体制の網羅性同士は比較しない。同一箇所・同一事象を指すものを「一致」、片方のみを「単独検出」とし、検出元を明記して `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類する。
- Codex 側が fail-soft で終わった場合、gate は Claude 側だけで成立し、warning を `reviews/` に残す（final review 側の warning はさらに `ship-change` の既存経路で MR/PR description にも転記する）。`command -v codex` が成立せず並走がそもそも始まらなかった場合も fail-soft と同様に扱い、warning を `reviews/` に残す。
- final review はさらに `review_snapshot_id` に束縛する: snapshot ID が変われば final review 本体と同様に Codex 側も再実行する。
- off スイッチ: `~/.claude/data/harness/cross-model-off` が存在すれば**並走のみ**無効化する（`command` モードの ci-monitor は対象外）。ファイル存在ベースなのは、Bash tool がセッション開始時の環境を継承し途中の `export` が走行中の controller に効かないため。
