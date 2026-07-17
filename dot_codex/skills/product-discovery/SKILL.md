---
name: product-discovery
description: 曖昧な機能アイデアを対話で実装可能な仕様へ整える。ブレインストーミング、要件整理、仕様を詰めたい、インタビューしてほしい、解決策やUXが未確定という依頼で使う。明確な仕様の実装や不具合原因の調査には使わない。
---

# Product Discovery

目的と利用者を起点に対話し、実装へ渡せる仕様を作る。コードを変更しない。実行計画も作成しない。

## 対話

- 最初にGoal、Context、Constraints、既知の前提を把握する。
- 必要なら既存プロダクトやコードをread-onlyで確認する。
- 一度に1〜3個の重要な質問だけを行い、回答を待つ。
- ユーザーの解決案を目的と分け、前提、非目標、失敗条件を問い直す。
- 選択肢がある場合は、利点、欠点、影響、推奨案を簡潔に示す。
- 利用者の主要フロー、例外、互換性、運用、観測方法を必要な範囲で確認する。
- 高影響な未決事項は残し、可逆な細部は根拠付きで仮定する。

## 停止条件

- ユーザーが探索だけを求めた場合は、案と未決事項を報告して止める。
- 実装、ファイル編集、実行計画、外部writeを行わない。
- 十分に明確になる前に質問票や完成仕様を一括提示しない。

## 仕様brief

合意できた内容を次の順で簡潔にまとめる。

1. Goalと利用者
2. ContextとConstraints
3. Non-goals
4. Requirementsと主要フロー
5. Decisionsと検討した代替案
6. Edge casesと運用上の注意
7. Done when
8. Open questions

handoff前に`~/.codex/review-policy.md`の仕様briefレンズでリスクを分類する。軽微はself-review、通常はread-only fresh reviewer、高リスクは該当する最大2レンズで確認し、Critical / Importantを解消する。Follow-upは仕様を勝手に拡張せず分離する。

ユーザーが実装へ進む場合は、承認されたbriefを`software-delivery`へ渡す。確定事項を再質問しない。
