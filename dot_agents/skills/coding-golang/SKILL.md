---
name: coding-golang
description: Goコードの読解・修正・実装・レビュー時に使用。並行処理、エラー処理、リソースライフサイクルを扱う。
invocation: auto
ecc-imports:
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: skills/golang-patterns/SKILL.md
    sections-merged: []
    conflicts:
      - "When to Activate"
      - "Core Principles"
      - "Error Handling Patterns"
      - "Concurrency Patterns"
      - "Interface Design"
      - "Package Organization"
      - "Struct Design"
      - "Memory and Performance"
      - "Go Tooling Integration"
      - "Quick Reference: Go Idioms"
      - "Anti-Patterns to Avoid"
    imported-at: 2026-04-27T00:00:00+09:00
---

# Go Coder (coding-golang)

## 概要

汎用的なGo言語のコード作成を支援するスキル。対象リポジトリの Go version、既存アーキテクチャ、ライブラリ、生成方法を確認し、その規約を優先する。

## 対応する開発タスク

- 新規機能の実装
- 既存コードのリファクタリング
- バグ修正
- APIエンドポイントの追加
- データベースモデルとクエリの作成
- ミドルウェアの実装
- ビジネスロジックの実装

## コード品質チェックリスト

コード作成時に以下を確認すること：

### 必須項目

- [ ] プロジェクトの既存規約に従っている
- [ ] Goのコーディング規約に準拠している
- [ ] 適切なエラーハンドリングを実装している
- [ ] ロガーを適切に使用している
- [ ] コンテキストを伝播させている
- [ ] エクスポートされる要素にコメントを記述している
- [ ] 早期リターンでネストを浅く保っている
- [ ] 関数は単一責任を持っている
- [ ] 原子性が必要な複数の永続化操作が、対象データストアのトランザクション境界で保護されている

### 設計品質

- [ ] テスタブルな設計になっている（依存性注入）
- [ ] インターフェースは小さく保たれている
- [ ] 適切なパッケージ構成になっている

## 実装フロー

1. **既存コードの調査**: プロジェクト構造、類似機能の実装、規約の把握
2. **要件の整理**: 実装する機能、変更する契約、影響範囲の特定
3. **設計**: 既存アーキテクチャ、エラーハンドリング、並行処理分析（下記参照）

必要に応じてリファレンスドキュメントを参照し、プロジェクト固有の規約とGoのベストプラクティスに従ったコードを作成すること。
テスト作成時は testing-golang、レビュー時は reviewing-golang を発動すること。

## Go ビルド検証

### ビルドタグ付きファイルの検証

変更ファイルに build constraint がある場合、実際の tag、対象 package、リポジトリの正規検証入口を確認する。その入口が tag を含まない場合は、実際の tag を渡して該当 package がコンパイルされる検証を追加する。

### コード生成後の差分確認

対象リポジトリの生成入口を実行した後は `git status` で全出力先を確認し、必要な生成物の漏れや依頼外差分がないことを確かめる。
