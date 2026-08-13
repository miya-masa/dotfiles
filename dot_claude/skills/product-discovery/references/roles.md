# role と委譲の規律（Claude Code）

workflow の各 role を Claude Code の subagent へ対応付ける表と、起動時の規律。レビューの観点定義そのものは `~/.agents/workflows/software_delivery/references/review-lenses.md`、共通制約は同 `review-common.md` にある。

## role 対応表

| workflow 上の role | Claude Code | 起動 model / effort |
|---|---|---|
| controller | 本体セッション | 既定（Opus 5 / high） |
| specification / planning | **委譲しない**。controller が spec と plan を書き、`reviewer` が反証する | — |
| plan reviewer（plan review gate） | `reviewer` | opus xhigh。spec が十分なら **skip**（条件は `implementation-planning`）。観点は spec 整合性と実装可能性だけ |
| explorer（事実収集） | `explorer` | sonnet / medium |
| implementer（1 task 実装） | `implementer` | sonnet / xhigh |
| final reviewer（差分全体） | `reviewer` | **fable** xhigh |
| lens reviewer（レンズ個別） | `reviewer` | opus xhigh |
| Holistic reviewer（レンズ並列時の統合 1 本） | `reviewer` | **fable** xhigh（枯渇時 opus xhigh）。レンズを分けて並列にする時は既定で 1 本追加する |
| クロスモデル並走検証（spec review gate / final review、herdr 限定） | Codex（`herdr-delegate` の `agent` モード） | `effort=high`（Claude subagent ではないため tier 表とは別軸） |
| verifier（実入口 evidence） | `verifier` | sonnet / medium |
| debugging（原因が割れない時） | `explorer` を read-only 診断で起動。割れなければ `codex:codex-rescue` | sonnet / medium |

`reviewer` は read-only（`Edit` / `Write` を持たない）。`implementer` は commit / push / subagent 起動をしない。

**review gate は spec review と final review の 2 つだけ**で、task 単位の review subagent も preflight も置かない（同じ差分を二重に見ないため）。この 2 つは品質の要なので effort を下げない。

Security レンズは fable で起動しない（強化対象外で、分類器の refusal リスクがある）。

### 公認フォールバック

**fable が枯渇している時に限り** final reviewer を opus xhigh へ切り替えてよい（切り替えた旨を報告に 1 行残す）。それ以外の理由で指定 agent / model が起動できない場合は、勝手に下位 tier へ降格して続行せず、作業を中断してエラー原文をユーザーへ提示する。

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

- **model を必ず明示指定する。** 省略するとセッションの model（最も高価な tier）を継承し、model 選択の意味が消える。ただし turn 数が価格に効くので、最下位 tier を既定にはしない。
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
- 返ってきたら要約を読み、変更が衝突していないか確認し、全体テストを通してから統合する。

## 採用判定

reviewer は severity で足切りしない設計なので、絞り込みは controller の採用判定が本番。全指摘を一次情報（spec 本文 / diff / コード / 実行結果）で裏取りし、`今回修正 / 見送り（根拠付き）/ 要判断` に分類する。裏取りせずに採用も却下もしない。diff 全体を controller が読み直すことはせず、指摘箇所をスポットで読む。

`/code-review` はトークン固定費が重いため自動発火させず、ユーザーが明示起動した時だけ使う。`codex-doublecheck`（ユーザー明示指示による 1 周のクロスモデル確認 wrapper）も既定フローに含めない。ただし herdr 内の spec review gate と final review では、別契約 `herdr-delegate` による Codex 並走が既定 ON（詳細は下記「herdr 内クロスモデル並走」）。両者は別物: `codex-doublecheck` はユーザーが個別に呼ぶ 1 周確認、herdr 並走は 2 つの review gate に自動で相乗りする独立反証。

## herdr 内クロスモデル並走（spec review gate / final review）

`HERDR_ENV=1` かつ `~/.claude/data/harness/cross-model-off` が存在しない かつ `command -v codex` が成立する時、`product-discovery` の spec review gate と `execute-plan` の final review は、既定で Opus/fable reviewer と同時に Codex（`herdr-delegate` の `agent` モード）を起動する。判定はこれら呼び出し元 skill が行い、共有契約 `herdr-delegate` は関知しない。**review gate の数は増えない**（既存の 2 つの gate に Codex が相乗りするだけ）。

- Codex への入力は spec review では spec 全文、final review では diff + spec + plan のみ（0-context、scratch 隔離で機構的に担保）。前周の finding や Opus/fable 側の結論は渡さない。
- 両者の結論は互いに共有しない。
- 突き合わせは finding 単位。Opus/fable 側は複数レンズが各自の領分を見るのに対し Codex は全観点を 1 体で見るため、体制の網羅性同士は比較しない。同一箇所・同一事象を指すものを「一致」、片方のみを「単独検出」とし、検出元を明記して `採用 / 却下（根拠付き）/ 要ユーザー判断` に分類する。
- Codex 側が fail-soft で終わった場合、gate は Opus/fable 側だけで成立し、warning を `reviews/` に残す（final review 側の warning はさらに `ship-change` の既存経路で MR/PR description にも転記する）。`command -v codex` が成立せず並走がそもそも始まらなかった場合も fail-soft と同様に扱い、warning を `reviews/` に残す。
- final review はさらに `review_snapshot_id` に束縛する: snapshot ID が変われば final review 本体と同様に Codex 側も再実行する。
- off スイッチ: `~/.claude/data/harness/cross-model-off` が存在すれば**並走のみ**無効化する（`command` モードの ci-monitor は対象外）。ファイル存在ベースなのは、Bash tool がセッション開始時の環境を継承し途中の `export` が走行中の controller に効かないため。
