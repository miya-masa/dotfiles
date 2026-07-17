# Global Claude Code Instructions

@~/.agents/AGENTS.md

4原則は AGENTS.md 参照。以下は Claude Code 固有の運用メモ。

## Subagent
- **汎用フェーズ agent (4種)**: `explorer`(調査/read-only) / `implementer`(実装+テスト) / `reviewer`(spec照合+品質) / `verifier`(実入口検証)。controller(本体)は計画・仕様判断・最終判断を担うオーケストレータ。ワークフローは `feature-development` / `bugfix` skill が指揮書。レビュー観点(reviewing-golang / database-review / security-review / 言語 skill)は起動時に装着する。「調査のみ」「テスト追加のみ」は agent を単発起動。
- **モデル方針**: 設計・スコープ確定=controller(重い代替案検討・アーキ設計は opus subagent へ委譲可) / spec-review=controller 直 / 実装=implementer(sonnet) / 一次レビュー=reviewer(opus。frontmatter 固定) / 探索=explorer(sonnet)・検証=verifier(sonnet) / IoT設計(iot-data-pipeline-architect)=opus。**fable での subagent 起動はユーザーが明示指定した時のみ**(Fable トークン消費のため)。env `CLAUDE_CODE_SUBAGENT_MODEL` は設定しない(per-invocation `model` で制御)。
- **保護対象(public API・DB schema・認証認可・課金・migration・外部契約)や大規模変更のレビュー**は、モデルは opus のまま、レンズ並列(設計3: Completeness/Soundness/Operability、実装後4: Correctness/Robustness/Security/Contract)を `dispatching-parallel-agents` 経由でフレッシュ起動して厚みを出す。雛形と採用判定は `~/.agents/skills/feature-development/references/review-lenses.md`。
- **effort**: explorer/verifier=medium、implementer/reviewer=xhigh(frontmatter 指定済み)。複雑な調査は per-invocation で上書き可。session effortLevel(`xhigh`) は controller の計画品質に効くため据え置く。
- **haiku 降格の可否**: 定型・read-only・判断が軽い雑用(inventory 集計・ファイルスキャン・整形・分類・即答系ルックアップ・テスト/ビルド/lint 実行のみの verifier)は `model="haiku"` で委譲してよい。実際の入口(CLI/API/画面/デバイス)を動かす検証は sonnet のまま。root cause 特定・コード品質判断・設計・implementer/reviewer は haiku に落とさない(実装失敗の手戻りループが節約分を食うため)。
- **モデル枯渇時のフォールバック禁止**: implementer の sonnet や reviewer の opus が使えなくなっても、勝手に fable/haiku へ降格して継続しない。作業を中断し、リセット待ちか続行モデル(例: fable)かをユーザーに承認を求める(無断降格は意図しない品質低下を招くため)。
- **外部サービス操作はサブエージェントに委譲しない**(subagent は親セッションの接続を継承しない)。外部サービスの呼び出しは controller 直。ファイルベース収集(トランスクリプト走査・ログ集計)や長文の執筆・整形は haiku/sonnet subagent に委譲し、成果物はファイル経由で受け渡す(controller の context に全文を入れない)。

## Controller 行動規律(コンテキスト節約)
- 最大コストは出力ではなく**コンテキストの肥大**(一度読んだものは毎ターン再課金される)。委譲判断の基準は作業の難易度ではなく「controller のコンテキストに何トークン入るか」。
- 2〜3ファイル以上読む見込みの探索は explorer に委譲し、要約だけ受け取る。
- レビューで diff 全体を自分で読まない。reviewer の報告を受け、指摘箇所のみスポット Read で裏取りする。
- 損益分岐: 指示文を書くコスト ≈ 作業そのもの なら直接やる(1ファイル数行の修正は controller 直)。計画・仕様判断・指示文の作成・最終レビュー判断に controller を集中投資する。

## Workflow
- **新規ブランチでの実装は、先に `worktrunk:worktrunk` skill で worktree を作ってから**(`wt switch --create <branch>`)。例外: 既存ブランチ上の軽微な修正(1ファイル数行)や調査のみ。
- commit / push / PR 作成の前に `git rev-parse --show-toplevel` で CWD が意図したリポジトリ/worktree であることを確認する。
- **レビュー gate**: `writing-plans` 起動の前に設計レビュー(spec-review 最低1パス)、push/PR 作成の前に**フレッシュな reviewer レビュー**(セルフレビューは確証バイアスがあり代替にならない)。軽微 diff(<= 40 行 かつ <= 3 ファイル)では省略できる。
- ワークフロー `/code-review` はトークン固定費が重いため自動発火させず、ユーザーが明示起動した時だけ使う。既定の実装後レビューの最低ラインは reviewer agent、大規模・保護対象はレンズ並列で代替する。

## Tools
- 設定は `~/.claude/settings.json`(permissions/hooks/env)。hooks は危険操作・format/lint・検証漏れガードに限定。
- superpowers / 各 skill は道具。必須 gate ではなく規模に応じて Claude が判断して使う。
