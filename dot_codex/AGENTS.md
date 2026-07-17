# Codex Agent Instructions

目的は、要件を満たし既存挙動を壊さない、動作確認済みの最小差分を出すこと。

## 作業原則

- 依頼範囲外を変更しない。既存の未コミット変更はユーザーの作業として保持する。
- 不明点は可逆な仮定で進め、完了報告に仮定を一行で示す。
- protected contract（public API、DB schema、認証認可、課金、データ移行、外部契約）は黙って変更しない。
- commit、push、PR、外部 write、production 変更、破壊的操作は明示依頼なしに行わない。
- 曖昧な機能は `product-discovery`、原因不明の不具合は `systematic-debugging` で整理し、非自明な変更は `software-delivery` で実装する。
- 成果物のself-reviewとfresh reviewは `~/.codex/review-policy.md` の成果物別・リスク別の粒度に従う。
- native subagent は、共有状態や順序依存のない独立作業にだけ使う。
- 既存の流儀に合わせ、不要な抽象化や将来拡張を加えない。

## 検証と報告

- 変更リスクに比例したテスト、build、lintを行い、可能なら実際の入口から確認する。
- テストをskipまたは削除して成功扱いにしない。失敗は原因を直す。
- 完了時は変更内容、実行した検証と失敗履歴、残リスク、人間の判断が必要な点を簡潔に報告する。
