---
name: tdd
description: TDD、テストファースト、レッド・グリーン・リファクタで実装する時に使用。
ecc-imports:
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: agents/tdd-guide.md
    sections-merged: []
    conflicts:
      - "Your Role"
      - "TDD Workflow"
      - "Test Types Required"
      - "Edge Cases You MUST Test"
      - "Test Anti-Patterns to Avoid"
      - "Quality Checklist"
      - "v1.8 Eval-Driven TDD Addendum"
    imported-at: 2026-04-27T00:00:00+09:00
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: skills/tdd-workflow/SKILL.md
    sections-merged: []
    conflicts:
      - "When to Activate"
      - "Core Principles"
      - "TDD Workflow Steps"
      - "Testing Patterns"
      - "Test File Organization"
      - "Mocking External Services"
      - "Test Coverage Verification"
      - "Common Testing Mistakes to Avoid"
      - "Continuous Testing"
      - "Best Practices"
      - "Success Metrics"
    imported-at: 2026-04-27T00:00:00+09:00
---

# TDDガイド

## 概要

TDDで機能追加や不具合修正を進めるための、短い反復手順と判断基準を示す。原則として「失敗の確認」を必須とする。

## 基本ワークフロー

1. 仕様を最小の振る舞いに分解する。
2. Red: 失敗するテストを書く。
3. Red確認: 意図した理由で失敗するのを確認する。
4. Green: 最小実装でテストを通す。
5. Green確認: 全テストが通ることを確認する。
6. Refactor: テスト維持のまま設計を改善する。
7. 1つの振る舞いごとにサイクルを繰り返す。

## 鉄則

- 失敗テストなしで本番コードを書かない。
- 失敗を見ていないテストは無効とみなす。
- 例外が必要なら人に相談する。

## テスト設計の指針

- 仕様を例で表現する。
- 失敗理由が1つになるようにする。
- I/O境界と純粋ロジックを分ける。
- テスト名は「条件\_期待結果」など意図が分かる形にする。

## Greenの指針

- 最小のコードで通す。
- 早すぎる抽象化を避ける。
- まずはハードコードで通してもよい。

## Refactorの指針

- 重複を削減し、命名と責務を整える。
- 既存テストが通ることを維持する。
- テストが不足している場合は先に追加する。

## よくある失敗と対処

- 失敗テストなしで実装する → 実装を削除してRedからやり直す。
- テストがすぐ通る → 既存挙動の可能性があるためテストを見直す。
- 「簡単だから省略」 → 省略せず最小のテストを1つ書く。

## つまずいた時

- テストが難しい → 仕様や設計を簡素化し、扱いやすいAPIにする。
- モックだらけ → 依存を切り出し、境界の設計を見直す。

## 検証チェックリスト

- 新しい振る舞いごとにテストを書いた。
- Redの失敗を確認した。
- 失敗理由が意図通りだった。
- Greenで全テストが通った。
- Refactor後も全テストが緑のまま。
- テスト出力に警告やエラーがない。

## 依頼対応の進め方

- まず振る舞いを確認し、最小のテストケースに落とす。
- 1サイクルずつ進め、各段階の差分を明確に示す。
- 既存テストがある場合は整合性を確認する。

## ECC 由来: agents/tdd-guide.md

> ECC base commit `4e66b2882da9afb9747468b08a253ca2f09c85f3` の `agents/tdd-guide.md`（91 行、英語）を検証したが、本 skill のコンパクトな日本語ガイド構造と異なるため統合せず、**全 H2 を conflicts として記録**。
>
> ECC 由来 H2 と本 skill との対応:
>
> - **TDD Workflow** → 本 skill §基本ワークフロー で同等（既存優先）
> - **Quality Checklist** → 本 skill §検証チェックリスト で同等（既存優先）
> - **Edge Cases You MUST Test** / **Test Anti-Patterns to Avoid** / **Test Types Required** / **v1.8 Eval-Driven TDD Addendum** → 本 skill になし。**将来取り込み余地あり**（references/ecc-tdd-guide.md として配置するか、特定章を本文に追記する選択肢）

## /ECC 由来: agents/tdd-guide.md

## ECC 由来: skills/tdd-workflow/SKILL.md

> ECC base commit `4e66b2882da9afb9747468b08a253ca2f09c85f3` の `skills/tdd-workflow/SKILL.md`（463 行、英語）を検証したが、本 skill のコンパクトな日本語ガイド構造と異なるため統合せず、**全 H2 を conflicts として記録**。
>
> ECC `tdd-workflow` は包括的な TDD Workflow 解説:
>
> - **重複領域** (本 skill と概念重複): When to Activate / Core Principles / TDD Workflow Steps / Testing Patterns / Best Practices / Common Testing Mistakes to Avoid
> - **既存になし** (将来取り込み余地あり): Test File Organization / Mocking External Services / Test Coverage Verification / Continuous Testing / Success Metrics
>   - `testing-golang` skill の references/ や `tdd` skill のリファレンス追記で取り込む選択肢あり（本 spec のスコープ外）

## /ECC 由来: skills/tdd-workflow/SKILL.md
