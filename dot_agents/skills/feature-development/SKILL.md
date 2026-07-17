---
name: feature-development
description: "機能開発のワークフロー（計画→探索→実装/テスト→レビュー→検証）を controller がオーケストレーションするための指揮書。新機能・機能追加・既存挙動の変更で使う。各フェーズで explorer/implementer/reviewer/verifier の汎用 agent を起動する。「機能を実装」「機能開発」「feature を追加」などで参照。"
---

# Feature Development ワークフロー

controller は計画と最終判断を担うオーケストレータであり、探索・実装・レビュー・検証は可能な限り subagent に委譲する。計画は人間が直接レビューするため controller が担当する。

## Runtime と role の対応

本文中の role 名は論理名である。Claude Code では `explorer` / `implementer` / `reviewer` / `verifier`、Codex では同じ責務を持つ native subagent を起動する。他の runtime でも、各 role の read/write 境界と返却契約を保てる同等手段を使う。

## フェーズと担当

| フェーズ | 担当 | 使う skill | 人間に見せるもの |
|---|---|---|---|
| 1. 計画 | controller | brainstorming → writing-plans | plan |
| 1.5 仕様レビュー | controller（重い時は reviewer） | `spec-review` | Gap と v1 必要性 |
| 2. 探索 | explorer（観点別に並列可） | systematic-debugging / codebase-onboarding | 重要ファイルと発見 |
| 2.5 worktree | controller | runtime の worktree 手段 | 作業 worktree / branch |
| 3. 実装+テスト | implementer | test-driven-development + 言語 skill | タスクごとの差分 |
| 4. レビュー | fresh reviewer + implementer | review skill + 簡素化観点 | Critical / Important の指摘と反映 |
| 5. 検証 | verifier | verification-before-completion | 検証 evidence |
| 6. 出荷 | controller | [ship-gate.md](references/ship-gate.md) | sanitize / PR / CI |
| 終端 | controller | finishing-a-development-branch | 変更 / 検証 / 残リスク / 判断点 |

## 運用ルール

- 重い作業やブランチを切る作業では、実装前に active runtime の worktree skill/helper を使って隔離 worktree を作る。専用手段がなければリポジトリ規約に従って `git worktree` を使う。軽微な変更や read-only 調査では省略できる。
- implementer は既定で 1 タスク 1 起動の直列。共有状態・順序依存がなく、別 worktree で完結する独立タスクが 2 つ以上ある時だけ並列化する。
- read-only role は独立タスクなら並列可。write を伴う role は、別 worktree・共有ファイルなし・順序依存なしをすべて満たす場合だけ並列化する。verifier は source を編集せず test / build / temporary artifact だけを生成する。
- 言語 skill は role 起動時に controller が指定する（Go: coding/testing/reviewing-golang、Python: python-patterns/python-testing）。
- subagent の報告は鵜呑みにせず、controller が diff、コード、実行結果で裏を取る。
- public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約は protected contract とする。曖昧なまま変更せず、着手前にユーザー判断を得る。
- 「調査のみ」「テスト追加のみ」はフル workflow を通さず、対応 role を単発起動してよい。

## フェーズ 1-1.5: 計画と仕様レビュー

1. 要件、既存仕様、影響範囲、外部契約、完了条件を整理する。
2. 軽微な変更を除き、`spec-review` を最低 1 パス通してから plan を確定する。
3. 大規模、複雑、または protected contract に触れる場合は、設計 3 レンズ（Completeness / Soundness / Operability）を fresh reviewer に分けて並列委譲する。詳細は [review-lenses.md](references/review-lenses.md)。
4. 各 Gap に v1 必要性を付け、必要以上にスコープを増やさない。

runtime の hook に依存せず、controller 自身がこの gate の実施を確認する。

## フェーズ 2-3: 探索、worktree、TDD

- explorer に重要ファイル、既存パターン、呼び出し元、テスト入口、protected contract を調べさせる。観点が独立していれば並列化する。
- worktree gate を通過してから implementer を起動する。
- implementer は failing test または再現確認を先に作り、失敗を確認してから最小実装で green にする。テストの skip/delete で通さない。
- タスクごとに差分と focused test を確認し、次の依存タスクへ進む。

## フェーズ 4: fresh review と簡素化

実装文脈を持たない fresh reviewer を最低 1 体起動する。セルフレビューは確証バイアスがあるため代替にしない。

- reviewer は spec 適合、結合点、回帰、エラー処理を調べ、Critical / Important のみ報告する。
- 同じ review に reuse、重複、効率、不要な抽象化の削減も含める。修正は implementer に委譲する。
- 大規模または protected contract に触れる場合は Correctness / Robustness と、該当時 Security / Contract の fresh reviewer を並列起動する。詳細は [review-lenses.md](references/review-lenses.md)。
- controller は指摘を裏取りし、「今回修正 / 見送り（根拠付き）/ 要判断」に分類する。盲従しない。
- runtime 固有の review command はユーザーが明示した場合だけ追加で使い、既定 workflow の前提にしない。

## フェーズ 5-6: 検証と出荷

verifier は実際の入口に近い検証を fresh に実行し、command と結果を evidence として返す。controller は結果を確認してから [ship-gate.md](references/ship-gate.md) の review、sanitize、CI gate へ進む。CI が全 pass するまで完了を主張しない。

## 関連資料

- 論理分析: [analysis-techniques.md](references/analysis-techniques.md)
- レビューレンズ: [review-lenses.md](references/review-lenses.md)
- 出荷 gate: [ship-gate.md](references/ship-gate.md)
