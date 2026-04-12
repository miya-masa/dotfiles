---
name: coding-golang
description: Goコードの読み書きが発生する全てのタスクで使用。バグ調査・原因特定、バグ修正、新規機能実装、リファクタリング、コード読解・分析を含む。Goファイル(.go)の読み取りや修正案の作成が必要な場合に自動発動する。並行処理パターン、エラーハンドリング、chi/GORM等のプロジェクト規約を提供する。
invocation: auto
---

# Go Coder (coding-golang)

## 対応バージョン

| 項目     | バージョン |
| -------- | ---------- |
| Go       | 1.21+      |
| chi      | v5.x       |
| GORM     | v1.25+     |
| GORM-Gen | v0.3+      |

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

| ライブラリ                 | 用途                | 参照                                            |
| -------------------------- | ------------------- | ----------------------------------------------- |
| **chi**                    | HTTPルーター        | [chi-patterns.md](references/chi-patterns.md)   |
| **GORM / GORM-Gen**        | ORM（GORM-Gen優先） | [gorm-patterns.md](references/gorm-patterns.md) |
| **プロジェクト固有ロガー** | ロギング            | プロジェクト内のコードを参照                    |

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
- [ ] 複数のRepository書き込みがトランザクションで保護されている（[gorm-patterns.md](references/gorm-patterns.md) の「トランザクション境界設計」参照）

### ライブラリ固有

- [ ] GORM-Genが存在する場合は優先的に使用している

### 設計品質

- [ ] テスタブルな設計になっている（依存性注入）
- [ ] インターフェースは小さく保たれている
- [ ] 適切なパッケージ構成になっている

## リファレンス一覧

実装時には該当するパターンを参照すること：

| ファイル                                              | 内容                                                                |
| ----------------------------------------------------- | ------------------------------------------------------------------- |
| [chi-patterns.md](references/chi-patterns.md)         | chiルーターの使用パターン（ルーティング、ミドルウェア、認証）       |
| [gorm-patterns.md](references/gorm-patterns.md)       | GORM/GORM-Genの使用パターン（CRUD、リレーション、トランザクション） |
| [error-handling.md](references/error-handling.md)     | エラーハンドリングパターン（カスタムエラー、ラッピング）            |
| [coding-standards.md](references/coding-standards.md) | コーディング規約とベストプラクティス                                |
| [modern-go.md](references/modern-go.md)               | Go 1.21+の新機能（slog、errors.Join等）                             |
| [concurrency-patterns.md](references/concurrency-patterns.md) | 並行処理の実装パターン（遷移期間、Close()非破壊、抽象化境界） |

## 実装フロー

1. **既存コードの調査**: プロジェクト構造、類似機能の実装、規約の把握
2. **要件の整理**: 実装する機能の明確化、必要なエンドポイントやデータモデルの特定
3. **設計**: レイヤー構造（Handler → Service → Repository）、データモデル、エラーハンドリング、並行処理分析（下記参照）

必要に応じてリファレンスドキュメントを参照し、プロジェクト固有の規約とGoのベストプラクティスに従ったコードを作成すること。
テスト作成時は testing-golang、レビュー時は reviewing-golang を発動すること。

### 並行処理分析の必須手順

タスクが以下のいずれかに該当する場合、`references/concurrency-patterns.md` を **Read ツールで読み込んでから** 設計・実装を行うこと:

- 状態遷移やリソースのライフサイクル管理を含む
- クリーンアップ処理（Close, Shutdown等）が状態を書き込む
- interface実装（Repository等）を介した状態の保存・復元がある
- 複数のgoroutineやコネクションが同じリソースにアクセスする

リファレンスを読んだ上で、各パターンが該当するか判断し、該当するパターンを修正に適用すること。
新しい状態遷移を追加した場合、その状態を書き込む既存コードパス（Close/Shutdown等）が新しい遷移と安全に共存するか確認すること。

