---
name: product-discovery
description: 曖昧な機能アイデアを対話で実装可能な仕様へ整える。ブレインストーミング、要件整理、仕様を詰めたい、インタビューしてほしい、解決策やUXが未確定という依頼で使う。明確な仕様の実装や不具合原因の調査には使わない。
---

# Product Discovery

controllerは高影響なproduct判断だけをユーザーと合意し、コードやplanを変更しない。
詳細なartifact/packet形式は[spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md)を参照する。

## 対話とdispatch

- Goal、利用者、Context、Constraints、scope、non-goal、主要方針、失敗条件を確認する。事実はrepositoryを限定探索し、ユーザーへ尋ねない。
- `explorer`で事実を集め、要求が未確定ならnamed `specification`へ自己完結packetを渡してdraft/open decisionsを得る。
- 方針を2〜3案とtrade-offで示し、open decisionsを依存順に整理して各turn原則1問だけ質問する。回答ごとにevidence packetを更新し、事実/仮定/未決/Given-When-Thenを検査する。
- draft後は結論を互いに共有しないfresh Sol High reviewersを独立dispatchする。通常はCompletenessとSimplicity、protected contract/security/migration/並行状態時だけRiskを追加し、findingを採用・却下・ユーザー判断に分類して記録する。

## 停止とhandoff

- review反映済みspecをユーザーが明示承認するまでplanningや実装へ進まない（確認前はhandoffしない）。normative gapや証拠不足は`specification`へ戻す。
- short pathは明確な要求/AC/検証、局所1〜2ファイル、protected contract等なし、安全な変更分離の全条件が必要。controllerがshort-path task artifactを作成し、fresh Luna Max `task-reviewer` preflight後に限り`execute-plan`/`execute-and-ship`二択（追加されるshipping authorityを説明）を提示する。
- 通常のreview済みspec完了時は次phaseとして`implementation-planning`だけを案内し、plan review前の実装/実行選択は提示しない。探索だけならspecと未決で停止する。
- 仕様briefはGoal/利用者、Constraints、Non-goals、normative requirements、flow/edge、compatibility、AC、assumptions、open decisionsを含める。

reviewの判定は`~/.codex/review-policy.md`に従う。
