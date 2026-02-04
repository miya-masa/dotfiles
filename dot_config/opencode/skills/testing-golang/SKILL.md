---
name: testing-golang
description: Goのテストコード作成・修正が必要な時に使用するスキル。「テストコードを書いて」といった明示的な指示は当然、それ以外でも、テストコードの追加や修正が必要な場合は必ず使用する。
invocation: user
---

# Go Test Writer (testing-golang)

## 対応バージョン

| 項目              | バージョン |
| ----------------- | ---------- |
| Go                | 1.21+      |
| testify           | v1.9+      |
| mockery           | v2.x       |
| testcontainers-go | v0.30+     |

## 概要

Goのユニットテスト作成を支援するスキル。testifyフレームワークを使用したテーブル駆動テストと、testcontainersを活用した統合テスト、mockeryを使用したモック生成をサポートする。プロジェクト固有の規約に従い、包括的で保守性の高いテストコードを提供する。

## 重要: ドキュメント参照

**ライブラリの最新ドキュメントが必要な場合は、Context7 MCPツールを使用すること。**

```
# 例: testify の最新ドキュメントを取得
1. resolve-library-id で "stretchr/testify" を検索
2. query-docs でライブラリIDを使って必要な情報を取得
```

## プロダクトコードについて

**プロダクトコードの作成・修正が必要な場合は、`coding-golang` スキルを使用すること。**

```
/coding-golang
```

## テスト作成の基本原則

### 基本規約

| 項目                 | 規約                                                   | 備考     |
| -------------------- | ------------------------------------------------------ | -------- |
| ファイル命名         | `xxx_test.go` 形式                                     | Go標準   |
| ファイル比率         | プロダクトコード1ファイルに対してテストコード1ファイル | 推奨     |
| テストフレームワーク | testify を使用（assert、require、mock）                | Go標準的 |
| テストパターン       | テーブル駆動テストを基本                               | Go標準的 |
| モック生成           | mockery を使用                                         | 推奨     |
| 統合テスト           | testcontainers を使用                                  | 推奨     |

### テストパッケージパターン

Goのテストには3つのパッケージ宣言パターンがあります。チームで選択してください。

#### パターン1: 内部テスト（ホワイトボックス）

```go
package mypackage

import (
    "testing"

    "github.com/stretchr/testify/assert"
)

func TestInternalFunction(t *testing.T) {
    // プライベート関数・変数にもアクセス可能
    result := internalHelper("test")
    assert.Equal(t, "expected", result)
}
```

**特徴**: プライベート関数もテスト可能。実装詳細に依存するため、リファクタリング時にテストも修正が必要。

#### パターン2: 外部テスト（ブラックボックス - 標準）

```go
package mypackage_test

import (
    "testing"

    "github.com/stretchr/testify/assert"

    "your-project/internal/mypackage"
)

func TestPublicFunction(t *testing.T) {
    result := mypackage.PublicFunction("test")
    assert.Equal(t, "expected", result)
}
```

**特徴**: 公開APIのみテスト。パッケージ名プレフィックスが必要だが、実装詳細に依存しない。

#### パターン3: 外部テスト + ドットインポート（推奨）

```go
package mypackage_test

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    . "your-project/internal/mypackage" // ドットインポート
)

func TestPublicFunction(t *testing.T) {
    // パッケージ名なしで直接呼び出せる
    result := PublicFunction("test")
    assert.Equal(t, "expected", result)
}
```

**特徴**: 外部テスト（ブラックボックス）でありながら、コードの可読性が高い。

> **注記**: ドットインポートはテストコードでは**条件付き許容**（Go Code Review Comments）。
> testifyドキュメントでも使用例があり、チーム規約として採用可能です。

## テーブル駆動テストパターン

### 基本構造

```go
func TestFunctionName(t *testing.T) {
    tests := []struct {
        name    string
        input   InputType
        want    ExpectedType
        wantErr bool
    }{
        {
            name:    "success: basic case",
            input:   validInput,
            want:    expectedOutput,
            wantErr: false,
        },
        {
            name:    "error: invalid input",
            input:   invalidInput,
            want:    zeroValue,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := FunctionName(tt.input)

            if tt.wantErr {
                require.Error(t, err)
                return
            }

            require.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

### テストケース名の命名規則

```go
tests := []struct {
    name string
}{
    {name: "success: description"},    // 正常な動作
    {name: "error: description"},      // エラーケース
    {name: "edge case: description"},  // 境界値や特殊ケース
}
```

## testify の使い方

### assert と require の使い分け

| メソッド  | 用途               | 失敗時の動作       |
| --------- | ------------------ | ------------------ |
| `require` | 前提条件のチェック | テストを即座に中断 |
| `assert`  | 複数のアサーション | テストを継続       |

```go
// require: エラーの場合、テストを即座に終了
require.NoError(t, err)
require.NotNil(t, result)

// assert: エラーでもテストを継続
assert.Equal(t, expected, actual)
assert.True(t, condition)
```

### 主要なアサーションメソッド

```go
// 等価性
assert.Equal(t, expected, actual)
assert.NotEqual(t, expected, actual)

// nil チェック
assert.Nil(t, object)
assert.NotNil(t, object)

// エラーチェック
assert.NoError(t, err)
assert.Error(t, err)
assert.EqualError(t, err, "expected error message")
assert.ErrorIs(t, err, targetErr)  // errors.Is を使用

// ブール値
assert.True(t, condition)
assert.False(t, condition)

// コンテナ
assert.Contains(t, slice, element)
assert.Len(t, collection, expectedLength)
assert.Empty(t, collection)
```

## モック作成パターン

モックの作成には **mockery + testify/mock** の組み合わせを使用する。詳細は `references/mock-patterns.md` を参照。

### mockery によるモック生成

```bash
# インターフェースからモックを生成
mockery --name=UserRepository --output=mocks --outpkg=mocks
```

### testify/mock を使用したテスト

```go
package mypackage_test

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"

    "your-project/mocks"
)

func TestUserService_GetUser(t *testing.T) {
    // モックの作成
    mockRepo := mocks.NewMockUserRepository(t)

    // 期待する呼び出しを設定
    mockRepo.EXPECT().
        GetByID(mock.Anything, int64(1)).
        Return(&User{ID: 1, Name: "Test"}, nil).
        Once()

    // テスト対象の作成
    service := NewUserService(mockRepo)

    // テスト実行
    user, err := service.GetUser(context.Background(), 1)

    // アサーション
    assert.NoError(t, err)
    assert.Equal(t, "Test", user.Name)
}
```

詳細なモックパターンは `references/mock-patterns.md` を参照。

## エッジケースの考慮

テストを作成する際は、以下のエッジケースを必ず考慮すること。詳細は `references/edge-cases.md` を参照。

### よくあるエッジケース

- **ゼロ値**: 0, "", nil, 空スライス、空マップ
- **境界値**: 最小値、最大値、-1, 0, 1
- **空とnil**: nilと空のスライス/マップは異なる
- **特殊文字**: Unicode、改行、タブ、ヌルバイト
- **エラーパス**: 異常系の動作確認

## 統合テスト（testcontainers）

データベースや外部サービスとの統合テストには、testcontainersを使用する。詳細は `references/testcontainers-patterns.md` を参照。

```go
func TestDatabaseOperation(t *testing.T) {
    db, cleanup := setupPostgresContainer(t)
    defer cleanup()

    // テスト実行...
}
```

## 高度なテスト

ファズテスト、ベンチマークテスト、並列テストについては `references/advanced-testing.md` を参照。

## 品質チェックリスト

テスト作成時に以下を確認すること:

### 必須項目

- [ ] `xxx_test.go` の命名規則に従っている
- [ ] パッケージ名に `_test` サフィックスがついている
- [ ] testify の `assert`/`require` を使用している
- [ ] テーブル駆動テストパターンを使用している
- [ ] 正常系と異常系の両方をカバーしている
- [ ] エッジケースを考慮している
- [ ] テストケース名が説明的である

### モック使用時

- [ ] mockery で生成したモックを使用している
- [ ] モックの期待値が適切に設定されている
- [ ] `mock.Anything` の使用は必要最小限

### 統合テスト

- [ ] testcontainers を使用している
- [ ] クリーンアップ処理が適切に実装されている

## リファレンス一覧

| ファイル                                                            | 内容                                      |
| ------------------------------------------------------------------- | ----------------------------------------- |
| [mock-patterns.md](references/mock-patterns.md)                     | mockery + testify/mock、httptest パターン |
| [testcontainers-patterns.md](references/testcontainers-patterns.md) | PostgreSQL、MySQL、Redis コンテナパターン |
| [edge-cases.md](references/edge-cases.md)                           | エッジケースの包括的リスト                |
| [advanced-testing.md](references/advanced-testing.md)               | ファズテスト、ベンチマーク、並列テスト    |

必要に応じてこれらのリファレンスを参照し、包括的なテストを作成すること。
