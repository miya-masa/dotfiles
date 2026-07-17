---
name: spec-review
description: spec / plan の論理的な抜け漏れと運用観点を実装前に軽くレビューする時に使う。feature-development フェーズ 1.5 から呼ばれるほか、単体でも起動できる（「plan をレビュー」「仕様を確認」「実装前にチェック」「spec の抜け漏れ」など）。重い対話レビューはしない薄い skill。
---

# Spec Review

spec / plan を実装前に軽くレビューし、論理的な抜け漏れと運用上の穴を拾う。通常は controller が 1 パス行い、大規模または protected contract を含む場合だけ fresh reviewer に委譲する。role の runtime 対応は [feature-development](../feature-development/SKILL.md#runtime-と-role-の対応) を参照する。

## 使う場面

- `feature-development` の plan 確定前。
- 単体の spec / plan を実装前に確認する時。

アイデアの発散には brainstorming、コードのレビューには fresh reviewer と言語 / 専門 review skill を使う。1 ファイル数行の軽微な変更は対象外にできる。

## 進め方

1. **要約**: 解決する問題、方式、影響範囲、成功条件を 3-5 行で言い直す。要約できなければ曖昧さを Gap とする。
2. **論理**: [analysis-techniques.md](../feature-development/references/analysis-techniques.md) の決定表、状態遷移、不変条件、敵対的思考、境界、依存、時間軸から該当する観点だけ使う。
3. **運用**: 互換性、移行、ロールバック、観測性、テストを確認する。
4. **YAGNI**: 各 Gap に `v1 必須 / v1.x で可 / 将来拡張で十分` を付ける。記載がないだけでは必須にしない。
5. **結論**: `修正必須 / できれば修正 / 後回し可` に分類し、実装着手可否を出す。

大規模、複雑、または public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約に触れる場合は、[review-lenses.md](../feature-development/references/review-lenses.md) に従い Completeness / Soundness / Operability を別コンテキストの fresh reviewer に並列委譲する。

## 固定レビュー観点

- **問題設定**: 目的、非目標、制約、成功条件は明確か。
- **解決策**: 採用理由、代替案、トレードオフは妥当か。
- **影響と契約**: API、schema、job、client、運用者への影響と後方互換性は明確か。
- **データと状態**: 整合性、冪等性、順序、部分成功、移行、ロールバックを扱っているか。
- **失敗時挙動**: 検知、表示、retry 可否、復旧手順が定義されているか。
- **security**: 認証認可、secret、入力、信頼境界、監査性に穴がないか。
- **運用**: release、rollback、metrics、logs、traces、alerts が必要十分か。
- **test**: acceptance、境界条件、統合点、回帰範囲が検証可能か。
- **責務と順序**: 前提作業、依存、担当、実装順に矛盾がないか。

## レビュー姿勢

- 実装量が増える指摘は、安全性、互換性、データ整合性、法的要請などの正当性を添える。添えられなければ後回し可とする。
- 開いた質問だけで終えず、懸念、発生条件、推奨する最小修正をセットで出す。
- spec / plan は直接書き換えず、指摘を controller とユーザーへ返す。
- 過剰な章、表、将来拡張、依頼外 component の mitigation を追加しない。
- 外部 issue ID、ローカル path、secret、非公開情報を成果物へ混入させない。

## ユーザー判断が必要な分岐

AGENTS.md の「仮定で進める」に従い、曖昧でも可逆な選択は仮定を明示して進む。次の不可逆または protected contract の分岐だけ、active runtime の質問手段で着手前に選択肢を確認する。

- public API / DB schema / 認証認可 / 課金 / データ移行 / 外部契約の変更。
- 第三者公開 service の初採用、secret や社外秘の外部送信。
- rollback できない migration や production 変更。
- 依頼範囲そのものを広げる選択。
