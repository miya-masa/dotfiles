---
name: task
description: 新しい task を始める時の入口。task が切り替わる任意のタイミングで /task に続く自由文または依頼の冒頭から起動し、機能開発・バグ修正・軽量調査なら該当 skill へ渡し、どれにも当たらない汎用作業（設定変更・CI/CD 変更・依存更新・小さいリファクタリング・開発環境の整備・掃除・パッケージング・タグ打ち・実機での動作確認・docs とコードをまたぐ変更）はこの skill が最小手順で完了させる。「どう進める」「これから何する」「/task」「まず何を」などで使う。
---

# Task（task の入口）

依頼を分類し、専用 workflow があればそこへ渡す。どれにも当たらない汎用作業はこの skill が最後まで担う。作業量・委譲・effort は共通 [effort-policy.md](../../workflows/software_delivery/references/effort-policy.md) に従う。

**session lifecycle ではなく task lifecycle の入口。** セッション開始時に限らず、task が切り替わるたび（handoff からの再開、割り込み依頼、前 task の完了後）に起動してよい。既に走っている workflow の途中では起動しない。

## 分類

| 判定 | 進め方 | 強い signal |
|---|---|---|
| 機能開発 | `product-discovery` へ（下の機能開発ワークフロー） | 新しい挙動の実装、追加、意図的変更 |
| バグ修正 | `bugfix` へ | 既存挙動が壊れた、error、障害、修正要求 |
| 軽量調査 | `investigation` へ | コードを変えずに動作、場所、原因を調べる |
| 汎用作業 | **この skill で実行**（下の汎用作業） | 上のどれでもないが、コード・設定・環境・生成物を変える、または実機で確かめる |
| skill 不要 | 通常対応 | 質問、会話、記憶の想起、調べずに答えられること |

対象が明白なら分類と signal を 1 行で宣言して即進む。複数候補が残っても不可逆な分岐でなければ、最も可能性の高い分類を仮定し、その仮定を 1 行で明示して進む。protected contract や不可逆操作の選択に影響する場合だけ active runtime の質問手段で 1 問確認する。

**手を動かす依頼を「skill 不要」へ落とさない。** skill 不要は成果物が返答そのものである場合に限る。

委譲・並走・長時間コマンドの実行先を選ぶ時は [execution-topology.md](../../workflows/software_delivery/references/execution-topology.md) を参照する。Main Agent が選択理由と統合責任を持ち、専門 workflow へは選択結果だけ引き継ぐ。小さい直接作業では読み込まず、実行先選択のために workflow を二重起動しない。

## 機能開発ワークフロー

機能開発に分類したら、次の順で phase skill を渡り歩く。入口は `product-discovery`。

`product-discovery → implementation-planning → execute-plan → ship-change → post-merge-cleanup`

| ステップ | skill | 人間に見せるもの | 停止点 |
|---|---|---|---|
| 1. 発散・spec・spec レビュー | `product-discovery` | spec、Gap | spec の明示承認 |
| 2. 実行計画・plan レビュー | `implementation-planning` | plan、着手可否 | 実行方法の二択 |
| 3. 実行（worktree・実装・review・検証） | `execute-plan` | task ごとの差分、final review、実入口 evidence | `LOCAL_COMPLETE` |
| 4. 出荷 | `ship-change` | sanitize / MR・PR / CI | MR ready |
| 5. 後片付け | `post-merge-cleanup` | 削除対象の列挙と結果 | 終端 |

`execute-and-ship` はステップ 3〜4 の合成で、ユーザーがそれを選んだ時だけ shipping まで続けて走る。各 phase skill は末尾に次のステップと自分の非権限を持つので、そこに従う。**停止点をまたぐ権限（実装 / shipping / merge / cleanup）を skill をまたいで推論しない。**

明確・局所・可逆で protected contract 非該当、AC と検証が明確で委譲コストが作業を上回る小変更は、ファイル数を問わず直接実装・検証する。変更単位の完了にはrisk gate（v2 LOWは自動、MEDIUMはsummary、HIGHはboundaryの明示承認、v1 legacyは従来承認）を通す。正式な再開・shipping が必要なら `product-discovery` の short path、要求や境界が未確定なら通常経路を使う。

## 汎用作業

設定変更、CI/CD 変更、依存更新、小さいリファクタリング、開発環境の整備、掃除、パッケージング、タグ打ち、実機での動作確認、docs とコードをまたぐ変更、ハーネス自身の改修などが入る。ここでは他 skill へ渡さず自分で完了させる。

まず直接実行を既定にし、下の昇格条件に当たった時だけ軽量 plan を挟む。**ファイル数や行数で決めない。** 解法の不確実性・blast radius・残っている判断の量で決める。

| 経路 | 条件 |
|---|---|
| 直接実行 → 検証 | 解法が明確、局所、可逆、影響範囲が読めていて、検証手段が自明 |
| 軽量 plan → 実行 → 検証 | 下のいずれか 1 つで足りる |

- 複数箇所・複数リポジトリ・複数ステップに及び、順序を間違えると戻しにくい。
- 実装方法にまだ判断が残る、または scope の切り分け自体が成果物の一部。
- 失敗時の影響が大きい（外部サービス、配布物、環境、他人の作業を壊しうる）。
- 検証方法を先に決めないと「終わった」と言えない。

軽量 plan は `Goal` / `Scope`（やらないことを 1 行）/ `Plan`（手順 3〜6 行）/ `Validation`（実行する command と期待結果）だけ。これ以上作らない。書き始めて手順が 3 行に収まると分かったら plan を捨てて直接実行してよい。**workflow artifact、`context.json`、spec、phase 遷移、plan review subagent は作らない。** 提示して続行してよく、実行前の承認待ちは不可逆・外部影響のある手順に限る。実装変更の完了前は上記risk gateを適用する。

- 最小差分で既存の流儀に合わせる。ついで改善をしない（気付いた点は報告の残リスクへ）。
- 宣言した Validation を実際に実行する。実行できなかったものは「未検証」と書く。実機・外部環境での確認を代替（mock・dry-run）で済ませたなら、何で済ませたかを書く。
- 観測可能な挙動を変えたなら、回帰を検出できる検証を最低 1 つ通す。設定・docs・生成物だけの変更に形式的な failing test を要求しない。
- self-review の可否、fresh reviewer の人数・lens・failure route は共通 [review-common.md](../../workflows/software_delivery/references/review-common.md) に従う。Codex は同文書が参照する `~/.codex/review-policy.md` の canonical risk matrix を正本とし、ここで独自の免除条件を設けない。
- 実装変更は [review-common.md](../../workflows/software_delivery/references/review-common.md) のrisk分類を適用する。v2 LOWは人間待ちなし、MEDIUMはsummary、HIGHはboundaryの明示承認を要求し、v1 legacyは従来承認を維持する。[evidence-contract.md](../../workflows/software_delivery/references/evidence-contract.md#人間レビューの記録と操作) のhelperで現在の検査を行う。
- 破壊的・不可逆操作（push / tag / 配布 / 環境削除 / production 変更）は明示許可なしに実行しない。
- commit は依頼された範囲で `conventional-commit` に従う。push / MR まで求められたら、`bugfix` と同じく既存 evidence で `product-discovery` の short path から artifact を起こし、`ship-change` の gate を通す。shipping 権限を作業依頼から推論しない。

汎用作業の途中でも、専用 skill がある領域（チケット / リリース / 文面 / レポート / secret 取得 / 外部サービス操作）はその skill を使う。

## 境界

- 既存挙動が意図通りでないなら bugfix、新規挙動や意図的変更なら機能開発ワークフロー。
- 製品の外部挙動を意図的に増減させるなら機能開発ワークフロー、既存挙動を保ったまま実装・設定・環境・生成物を整えるだけなら汎用作業。汎用作業の途中で未決の要求や設計境界が出たら止めて `product-discovery` へ上げる。既存挙動が壊れており原因調査が要ると分かったら `bugfix` へ。
- 原因を答えるだけなら investigation、修正まで求めるなら bugfix。「原因調査と対応案がほしい」は investigation で、修正の実施が明示されて初めて bugfix。CI 失敗・障害という語だけで bugfix に倒さない。
- explorer role による追跡が必要なら investigation、即答できるなら skill 不要。
- コードを変えず成果物がドキュメント（仕様書・設計パケット・発表資料・会議アジェンダ・レポート）なら必要な証拠だけを直接調べて執筆する。独立した広い調査が必要な場合だけ investigation を使う。設計や企画の発散が必要なら先に product-discovery を通す。分類表に当てはまらないことを理由に skill 不要へ倒さない。
- skill / CLAUDE.md / settings.json などハーネス自身の改修は汎用作業として扱う。対象に専用 skill があればそれを優先し（settings.json の権限 / hook 変更は update-config 等）、未決の要求・設計境界がある場合だけ機能開発ワークフローに載せる。
- 指示動詞が無く参照ファイル / URL だけが渡された場合は、分類前にその参照を読む。読んでから分類する。

## ハンドオフ

専用 workflow へ分類したら、active runtime で対応 skill を起動し、元の依頼と分類上の補足を引き継ぐ。一度ハンドオフしたら、委譲先 workflow が主導する。skill 不要なら「skill を通さず直接対応する」と述べて通常対応する。

## 分類ログ

Claude Code runtime では、分類を決めたらハンドオフ（汎用作業なら着手）直前に `~/.claude/data/start-router/decisions.jsonl` へ必ず 1 行 append する（旧 `start` skill 由来の path。履歴を継続するため変えない）。ファイルが無ければ作成し、既存行を上書きしない。1 行は次の固定 schema の JSON object とする。

| key | value |
|---|---|
| `date` | 分類日（`YYYY-MM-DD`） |
| `input_summary` | sanitize した入力要約 |
| `classified` | handoff skill 名、汎用作業は `generic`、または `skill-none` |
| `confidence` | `high` / `medium` / `low` |
| `ambiguous` | `true` / `false` |
| `signal` | 分類根拠 1 文 |
| `note` | 迷い・改善のヒント。無ければ空文字 |
| `resolution` | 後から正否が分かれば追記。着手時は空文字可 |

Jira 本文、URL、secret、社外秘は記録しない。append 失敗で作業を止めない。集計や既存行の変更は行わない（追記のみ）。

他 runtime は同等の分類ログ機構を提供している場合だけ、sanitize した要約、分類、confidence、signal を記録する。Claude 固有 path を代用しない。


## 不変条件

- worktree、discovery、plan、実装、調査を二重起動しない。
- 委譲先が持つ review、verification、sanitize、CI gate を省略しない。
- 分類のためだけにユーザーへ質問せず、可逆な曖昧さは仮定で進める。
