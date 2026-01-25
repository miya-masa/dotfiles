---
name: coding-golang
description: Go言語のコード作成・修正が必要な時に使用するスキル。新規機能実装、リファクタリング、バグ修正、APIエンドポイント追加、データベースモデル・クエリ作成、ミドルウェア実装、ビジネスロジック実装などに対応。chi（HTTPルーター）、GORM/GORM-Gen（ORM）を使用したプロジェクトで特に有効。Goのベストプラクティスとプロジェクト規約に従った高品質なコードを生成し、エラーハンドリング、並行処理、RESTful API設計などGoの慣例を遵守する。
invocation: user
---

# Go Coder (coding-golang)

## 対応バージョン

| 項目 | バージョン |
|------|-----------|
| Go | 1.21+ |
| chi | v5.x |
| GORM | v1.25+ |
| GORM-Gen | v0.3+ |

## 概要

汎用的なGo言語のコード作成を支援するスキル。chiルーター、GORM/GORM-Gen、プロジェクト固有のロガーを活用し、Goのベストプラクティスとプロジェクト固有の規約に従った高品質なコードを提供する。

## 対応する開発タスク

- 新規機能の実装
- 既存コードのリファクタリング
- バグ修正
- APIエンドポイントの追加
- データベースモデルとクエリの作成
- ミドルウェアの実装
- ビジネスロジックの実装

## 重要: ドキュメント参照

**ライブラリの最新ドキュメントが必要な場合は、Context7 MCPツールを使用すること。**

```
# 例: chi の最新ドキュメントを取得
1. resolve-library-id で "go-chi/chi" を検索
2. query-docs でライブラリIDを使って必要な情報を取得
```

## 主要な技術スタック

| ライブラリ | 用途 | 参照 |
|-----------|------|------|
| **chi** | HTTPルーター | [chi-patterns.md](references/chi-patterns.md) |
| **GORM / GORM-Gen** | ORM（GORM-Gen優先） | [gorm-patterns.md](references/gorm-patterns.md) |
| **プロジェクト固有ロガー** | ロギング | プロジェクト内のコードを参照 |

## コード作成の基本原則

### 1. プロジェクト固有の規約を最優先

コード作成時は、以下を必ず確認すること：

1. **既存コードの調査**: プロジェクトの既存コードから規約とパターンを把握
2. **ディレクトリ構造**: プロジェクトのディレクトリ構造に従う
3. **命名規則**: 既存のファイル名、変数名、関数名のパターンを踏襲
4. **ロガーの使い方**: プロジェクト内のロガー使用例を参照
5. **エラーハンドリング**: プロジェクト内の既存エラーハンドリングパターンを確認

### 2. Goのベストプラクティス

- 明確で簡潔なコード
- 適切なエラーハンドリング（[error-handling.md](references/error-handling.md)参照）
- 早期リターンでネストを浅く保つ
- 小さく単一責任の関数
- インターフェースを活用した疎結合設計
- コーディング規約の遵守（[coding-standards.md](references/coding-standards.md)参照）

### 3. Go 1.21+ の新機能を活用

最新のGoの機能を積極的に活用する（[modern-go.md](references/modern-go.md)参照）：

- **slog**: 構造化ロギング
- **errors.Join**: 複数エラーの結合
- **slices/maps パッケージ**: 汎用スライス・マップ操作
- **clear**: マップ・スライスのクリア
- **max/min**: 組み込み関数

### 4. 基本的なコードパターン

```go
// 関数のドキュメントコメント
// CreateUser creates a new user with the given information.
func CreateUser(ctx context.Context, name, email string) (*User, error) {
    // 入力バリデーション（早期リターン）
    if err := validateUserInput(name, email); err != nil {
        return nil, err
    }

    // ビジネスロジック
    user := &User{Name: name, Email: email}
    if err := saveUser(ctx, user); err != nil {
        return nil, fmt.Errorf("failed to save user: %w", err)
    }

    return user, nil
}
```

## テストコードについて

**テストコードの作成・修正が必要な場合は、`testing-golang` スキルを使用すること。**

```
/testing-golang
```

このスキルは以下に対応：

- ユニットテストの作成
- テーブル駆動テストのパターン
- モックの作成
- 統合テストの作成

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

### ライブラリ固有

- [ ] GORM-Genが存在する場合は優先的に使用している

### 設計品質

- [ ] テスタブルな設計になっている（依存性注入）
- [ ] インターフェースは小さく保たれている
- [ ] 適切なパッケージ構成になっている

## リファレンス一覧

実装時には該当するパターンを参照すること：

| ファイル | 内容 |
|----------|------|
| [chi-patterns.md](references/chi-patterns.md) | chiルーターの使用パターン（ルーティング、ミドルウェア、認証） |
| [gorm-patterns.md](references/gorm-patterns.md) | GORM/GORM-Genの使用パターン（CRUD、リレーション、トランザクション） |
| [error-handling.md](references/error-handling.md) | エラーハンドリングパターン（カスタムエラー、ラッピング） |
| [coding-standards.md](references/coding-standards.md) | コーディング規約とベストプラクティス |
| [modern-go.md](references/modern-go.md) | Go 1.21+の新機能（slog、errors.Join等） |

## 実装フロー

### 新機能実装の手順

```
1. 既存コードの調査
   ├─ プロジェクト構造の確認
   ├─ 類似機能の実装を参照
   └─ 規約とパターンの把握

2. 要件の整理
   ├─ 実装する機能の明確化
   └─ 必要なエンドポイントやデータモデルの特定

3. 設計
   ├─ レイヤー構造（Handler → Service → Repository）
   ├─ データモデル定義
   └─ エラーハンドリング戦略

4. 実装
   ├─ モデル定義
   ├─ リポジトリ実装（GORM-Gen/GORM）
   ├─ サービス層（ビジネスロジック）
   ├─ ハンドラー（HTTPエンドポイント）
   └─ ミドルウェア（必要に応じて）

5. 品質確認
   ├─ コーディング規約の遵守
   ├─ エラーハンドリングの適切性
   ├─ ロギングの実装
   └─ コメントの追加

6. コードレビュー
   └─ reviewing-golang スキルを使用してレビュー
```

必要に応じてリファレンスドキュメントを参照し、プロジェクト固有の規約とGoのベストプラクティスに従った高品質なコードを作成すること。

## 実装完了時のレビュー

**実装が完了したら、必ず `reviewing-golang` スキルを使用してコードレビューを実施すること。**

```
/reviewing-golang
```

このスキルは以下を確認：

- goroutine安全性
- エラーハンドリング
- リソースリーク
- プロジェクト規約への準拠
