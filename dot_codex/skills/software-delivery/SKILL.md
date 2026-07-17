---
name: software-delivery
description: 確定済みまたは十分明確な仕様・診断briefに基づくコード変更を、実行計画、実装、レビュー、検証、出荷まで安全に進める。複数ファイルの変更、設計変更、長時間作業で使う。仕様探索や原因調査だけの依頼には使わない。
---

# Software Delivery

変更規模に合わせて工程を統合してよいが、完了条件と検証は省略しない。

## 前工程との接続

- 機能の目的や要件が曖昧なら、実装前に`product-discovery`で仕様briefを作る。
- 原因不明の不具合なら、修正前に`systematic-debugging`で診断briefを作る。
- 承認済みbriefがある場合は確定事項を再質問せず、このskillの仕様入力として扱う。

## 適用レベル

- 軽微: 1ファイル数行程度。仕様と計画、実行とself-reviewをまとめる。
- 通常: 複数ファイルまたは非自明な変更。6工程を通し、Plan modeで計画する。
- 長時間: 複数時間・複数セッション。`PLANS.md`形式のliving ExecPlanを使う。
- read-only: 調査、説明、レビューでは変更、検証、出荷へ勝手に進まない。

## 1. 仕様

- Goal、Context、Constraints、Done whenを確定する。
- 既存仕様、影響範囲、protected contractを確認する。
- 可逆な曖昧さは仮定し、高影響または不可逆な分岐だけ確認する。
- 不具合修正では、再現テストが修正前に失敗することを確認する。

## 2. 実行計画

- 非自明な変更はPlan modeでdecision-completeな計画にする。
- 通常作業の計画は会話内に置き、長時間作業だけExecPlanをファイル化する。
- 変更単位、完了条件、必要な検証、操作境界を明示する。
- 実装前に`~/.codex/review-policy.md`の実行計画レンズでレビューし、Critical / Importantを解消する。

## 3. 実行

- acceptance criteriaに沿う最小差分を実装する。
- 変更した振る舞いのテストを追加または更新する。
- native subagentは独立作業が明確に分けられる場合だけ使う。

## 4. レビュー

- `~/.codex/review-policy.md`でリスクを分類し、コードレンズでcorrectness、adversarial risk、regression、contract、test gap、product fit、simplicityを確認する。
- 軽微はself-review、通常はread-only fresh reviewer、高リスクは該当する最大2レンズでfresh reviewする。
- 一般的改善は非blocking Follow-upに分け、依頼なしに実装しない。
- 指摘を直したら影響箇所を再確認する。

## 5. 検証

- focused test、必要なbuild・lint・type checkを実行する。
- 可能ならAPI、画面、CLIなど実際の入口から確認する。
- command、成功・失敗履歴、未確認範囲を記録する。

## 6. 出荷

- commit、push、PR、CI監視、tag、releaseは明示依頼がある場合だけ行う。
- reviewとverificationが完了していなければ出荷しない。
- 外部writeや破壊的操作の承認は実行直前に一度だけ求める。
