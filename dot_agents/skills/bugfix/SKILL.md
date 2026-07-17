---
name: bugfix
description: "不具合修正のワークフロー（調査→再現→修正→検証）を controller がオーケストレーションするための指揮書。バグ・不具合・障害の修正で使う。explorer で原因特定、implementer で再現テスト→修正、verifier で検証。「バグを直して」「不具合修正」「この障害を調査して直す」などで参照。"
---

# Bugfix ワークフロー

controller はオーケストレーションと判断に集中し、調査・修正・fresh review・検証を subagent に委譲する。role の runtime 対応は [feature-development](../feature-development/SKILL.md#runtime-と-role-の対応) を参照する。

## フェーズと担当

| フェーズ | 担当 | 使う skill | 成果 |
|---|---|---|---|
| 1. 調査 | explorer | systematic-debugging | root cause 仮説と根拠 |
| 2. 再現 | explorer / verifier | project test tools | 最小再現と failing evidence |
| 2.5 worktree | controller | runtime の worktree 手段 | 隔離 worktree |
| 3. 修正 | implementer | test-driven-development + 言語 skill | 最小差分と green test |
| 4. fresh review | reviewer | 言語 / 専門 review skill | Critical / Important の指摘 |
| 5. 検証 | verifier | verification-before-completion | 実入口に近い evidence |
| 終端 | controller | finishing-a-development-branch | 固定形式の完了報告 |

## 調査

1. 症状、期待動作、再現条件、直近変更を整理する。
2. explorer に関連コード、呼び出し元、状態遷移、ログとテストを追わせる。
3. 対立仮説を作り、観測または実験で棄却する。症状ではなく root cause を特定する。
4. 次のいずれかなら、別コンテキストの fresh explorer または専門 reviewer に read-only 診断を委譲する。
   - コード上の予測と観測が矛盾する。
   - プロトコル、コーデック、ライブラリ内部などの専門知識が決め手になる。
   - 実機実験でしか対立仮説を判別できない。
   - 2 回の探索または同等の時間を使っても root cause が絞れない。
5. 追加診断には症状、仮説と棄却理由、関連パス、期待動作を渡す。返答は元の explorer / verifier が裏取りする。

調査のみの依頼はここで終了してよい。再現できず、検証可能な仮説も得られない場合は当て推量で変更せず、得られた evidence と不足情報を報告する。

## 修正

- ブランチを切る修正では、実装前に active runtime の worktree skill/helper、またはリポジトリ規約に沿う `git worktree` で隔離する。軽微な既存ブランチ修正は省略できる。
- failing reproduction test を先に確認し、最小修正で green にする。テストの skip/delete はしない。
- public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約へ波及するなら protected contract として止まり、変更前にユーザー判断を得る。
- ガード条件追加で済む場合は既存ロジックを大きく変えない。

## Review と検証

- 実装文脈を持たない fresh reviewer が仕様適合、回帰、失敗時挙動、修正の単純さを確認する。実装者のセルフレビューだけで終えない。
- verifier が再現手順、focused test、必要な統合テストを実行し、修正前に失敗した入口が修正後に成功する evidence を示す。
- controller は diff と実行結果を裏取りし、変更内容 / 検証（失敗履歴含む）/ 残リスク / 人間が判断すべき点を報告する。
