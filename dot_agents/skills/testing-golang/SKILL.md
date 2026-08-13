---
name: testing-golang
description: Goテストの作成・修正・設計で使用。並行処理テスト、モック、テーブル駆動テストを扱う。
invocation: auto
ecc-imports:
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: skills/golang-testing/SKILL.md
    sections-merged: []
    conflicts:
      - "When to Activate"
      - "TDD Workflow for Go"
      - "Table-Driven Tests"
      - "Subtests and Sub-benchmarks"
      - "Test Helpers"
      - "Golden Files"
      - "Mocking with Interfaces"
      - "Benchmarks"
      - "Fuzzing (Go 1.18+)"
      - "Test Coverage"
      - "HTTP Handler Testing"
      - "Testing Commands"
      - "Best Practices"
      - "Integration with CI/CD"
    imported-at: 2026-04-27T00:00:00+09:00
---

# Go Test Writer (testing-golang)

## 概要

Goのテスト作成を支援するスキル。対象リポジトリの package 構成、assertion / mock / 統合テスト基盤、実行 command を確認し、既存の選択を優先する。

## テスト作成の基本原則

振る舞いを直接確認できる場合はモックを増やさない。モックが必要な場合は、対象リポジトリの既存ツールと生成手順に従う。複数ケースを同じ不変条件で検証する場合はテーブル駆動テストを検討する。

## 品質チェックリスト

テスト作成時に以下を確認すること:

### 必須項目

- [ ] `xxx_test.go` の命名規則に従っている
- [ ] package 名は対象リポジトリの white-box / black-box test 方針に従っている
- [ ] プロジェクトの既存 assertion 手段を使用している
- [ ] ケースが複数ある場合、既存のテスト構造に合うならテーブル駆動にしている
- [ ] 正常系と異常系の両方をカバーしている
- [ ] エッジケースを考慮している
- [ ] テストケース名が説明的である

### モック使用時

- [ ] 対象リポジトリが生成モックを採用している場合、その生成ツールと手順に従っている
- [ ] モックの期待値が適切に設定されている
- [ ] 広すぎる matcher で重要な引数や呼び出し順を見落としていない

### 統合テスト

- [ ] プロジェクトの統合テスト基盤と実行 command を使用している
- [ ] クリーンアップ処理が適切に実装されている
