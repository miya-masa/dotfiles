---
name: start
description: セッション開始時に「どう進めるか」を判断するルーター。/start に続く自由文または依頼の冒頭で起動し、自由文を解析して機能開発・バグ修正・軽量調査・skill不要のどれかに分類し、該当 skill へハンドオフする。「どう進める」「これから何する」「/start」「まず何を」などで使う。判断とハンドオフだけを行い、実作業は委譲先 skill に任せる。
---

# Start（進め方ルーター）

依頼を分類して対応 skill へハンドオフする。計画、worktree、discovery、実装、調査そのものは行わない。

## 分類カテゴリ

| 判定 | ハンドオフ先 | 強い signal |
|---|---|---|
| 機能開発 | `product-discovery`（下の機能開発ワークフロー） | 新しい挙動の実装、追加、意図的変更 |
| バグ修正 | `bugfix` | 既存挙動が壊れた、error、障害、修正要求 |
| 軽量調査 | `investigation` | コードを変えずに動作、場所、原因を調べる |
| skill 不要 | 通常対応 | 軽い質問、会話、即答可能な設定変更 |

## 機能開発ワークフロー

機能開発に分類したら、次の順で phase skill を渡り歩く。入口は `product-discovery`。

`product-discovery → implementation-planning → execute-plan → ship-change → post-merge-cleanup`

| ステップ | skill | 人間に見せるもの | 停止点 |
|---|---|---|---|
| 1. 発散・spec・spec レビュー | `product-discovery` | spec、Gap と v1 必要性 | spec の明示承認 |
| 2. 実行計画・plan レビュー | `implementation-planning` | plan、着手可否 | 実行方法の二択 |
| 3. 実行（worktree・実装・review・検証） | `execute-plan` | task ごとの差分、final review、実入口 evidence | `LOCAL_COMPLETE` |
| 4. 出荷 | `ship-change` | sanitize / MR・PR / CI | MR ready |
| 5. 後片付け | `post-merge-cleanup` | 削除対象の列挙と結果 | 終端 |

`execute-and-ship` はステップ 3〜4 の合成で、ユーザーがそれを選んだ時だけ shipping まで続けて走る。各 phase skill は末尾に次のステップと自分の非権限を持つので、そこに従う。**停止点をまたぐ権限（実装 / shipping / merge / cleanup）を skill をまたいで推論しない。**

1 ファイル数行の軽微な変更は全ステップを通さず、実装 → self-review → 報告で済ませてよい。仕様が既に確定していて発散が不要なら `product-discovery` の spec review gate から始める（discovery 対話だけを省き、レビューと承認は通す）。局所的で AC と検証が明確な変更は、`product-discovery` の short path（task artifact + preflight review + 実行方法の二択）に載せる。

対象が明白なら分類と signal を 1 行で宣言して即ハンドオフする。複数候補が残っても不可逆な分岐でなければ、最も可能性の高い分類を仮定し、その仮定を 1 行で明示して進む。protected contract や不可逆操作の選択に影響する場合だけ active runtime の質問手段で 1 問確認する。

## 境界

- 既存挙動が意図通りでないなら bugfix、新規挙動や意図的変更なら機能開発ワークフロー。
- 原因を答えるだけなら investigation、修正まで求めるなら bugfix。「原因調査と対応案がほしい」は investigation で、修正の実施が明示されて初めて bugfix。CI 失敗・障害という語だけで bugfix に倒さない。
- explorer role による追跡が必要なら investigation、即答できるなら skill 不要。
- コードを変えず成果物がドキュメント（仕様書・設計パケット・発表資料・会議アジェンダ・レポート）なら investigation で調査した上で執筆まで続ける。設計や企画の発散が必要なら先に product-discovery を通す。分類カテゴリに当てはまらないことを理由に skill 不要へ倒さない。
- skill / CLAUDE.md / settings.json などハーネス自身の改修は、原則 skill 不要として controller が直接扱う。ただし対象に専用 skill があればそれを優先し、複数 skill への横展開や新規 skill 作成を伴う場合だけ機能開発ワークフローに載せる。
- 指示動詞が無く参照ファイル / URL だけが渡された場合は、分類前にその参照を読む。読んでから分類する。

## ハンドオフ

active runtime で対応 skill を起動し、元の依頼と分類上の補足を引き継ぐ。skill 不要なら「skill を通さず直接対応する」と述べて通常対応する。一度ハンドオフしたら、委譲先 workflow が主導する。

## 分類ログ

Claude Code runtime では、分類を決めたらハンドオフ直前に `~/.claude/data/start-router/decisions.jsonl` へ必ず 1 行 append する。ファイルが無ければ作成し、既存行を上書きしない。1 行は次の固定 schema の JSON object とする。

| key | value |
|---|---|
| `date` | 分類日（`YYYY-MM-DD`） |
| `input_summary` | sanitize した入力要約 |
| `classified` | handoff skill 名、または `skill-none` |
| `confidence` | `high` / `medium` / `low` |
| `ambiguous` | `true` / `false` |
| `signal` | 分類根拠 1 文 |
| `note` | 迷い・改善のヒント。無ければ空文字 |
| `resolution` | 後から正否が分かれば追記。着手時は空文字可 |

チケット本文、URL、secret、社外秘は記録しない。append 失敗でハンドオフを止めない。

他 runtime は同等の分類ログ機構を提供している場合だけ、sanitize した要約、分類、confidence、signal を記録する。Claude 固有 path を代用しない。

## 不変条件

- worktree、discovery、plan、実装、調査を二重起動しない。
- 委譲先が持つ review、verification、sanitize、CI gate を省略しない。
- 分類のためだけにユーザーへ質問せず、可逆な曖昧さは仮定で進める。
