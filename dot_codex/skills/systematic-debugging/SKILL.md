---
name: systematic-debugging
description: 原因不明の不具合、テスト失敗、障害、性能劣化、予期しない挙動を再現し、証拠からroot causeと修正条件を確定する。原因調査、再現して、なぜ失敗するか、直す前に調べたいという依頼で使う。原因と修正が既に明確な変更には使わない。
---

# Systematic Debugging

症状からroot causeまでを証拠でつなぎ、推測修正を防ぐ。このskillではコードを変更しない。

## 1. 症状を固定する

- Expected、Actual、発生条件、頻度、影響を分ける。
- 利用可能な最小の再現手順、失敗テスト、ログ、traceを確立する。
- 再現できない場合は、観測不足と製品不具合を区別する。

## 2. 境界を狭める

- 入力から症状までの実行経路と状態遷移を追う。
- 最近の変更、環境差、依存境界、並行性、永続化を必要な範囲で確認する。
- 正常な近接ケースと比較し、最初に期待から外れる地点を特定する。

## 3. 仮説を検証する

- 競合する仮説を少数列挙し、各仮説を反証できる確認を選ぶ。
- 一度に一つの変数だけを変え、結果を記録する。
- 証拠なしに複数修正を混ぜたり、症状を隠すguardを追加したりしない。
- root causeが未確定なら、確度と不足している証拠を明示する。

## 停止条件

- 調査だけの依頼では、診断briefを報告して止める。
- source、test、設定を編集せず、外部writeを行わない。
- 再現や証拠が不足したまま修正案を確定しない。

## 診断brief

1. SymptomとExpected / Actual
2. Reproduction
3. Root cause
4. Evidence
5. Impact scope
6. Regression test条件
7. Fix constraints
8. Unknowns

handoff前に`~/.codex/review-policy.md`の診断briefレンズでリスクを分類する。軽微はself-review、通常はread-only fresh reviewer、高リスクは該当する最大2レンズで、因果関係、競合仮説、影響範囲を確認する。証拠不足を防御的な修正案で埋めない。

修正も依頼されている場合は、確定したbriefを`software-delivery`へ渡す。原因調査を繰り返さず、再現テストから実装を始める。
