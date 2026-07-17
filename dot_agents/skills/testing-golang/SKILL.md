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

外部テスト + ドットインポートを推奨:

```go
package mypackage_test

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    . "your-project/internal/mypackage" // ドットインポート
)

func TestPublicFunction(t *testing.T) {
    result := PublicFunction("test")
    assert.Equal(t, "expected", result)
}
```

ブラックボックステストでありながら、パッケージ名プレフィックスなしで直接呼び出せるため可読性が高い。

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
- [ ] トランザクション内外の実行順序がモック期待値の順序と一致している（gomock使用時、トランザクション外操作→トランザクション内操作の順序で `EXPECT()` を定義。例: パスワード検証はトランザクション外なので先に、条件チェック・書き込みはトランザクション内なので後に期待値を設定する）

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
| [concurrency-testing.md](references/concurrency-testing.md)         | 並行処理のテストパターン（ライフサイクル、Repository抽象化、レース検出） |

### リファレンス読み込みの必須手順

タスクが以下のいずれかに該当する場合、対応するリファレンスを **Read ツールで読み込んでから** テストを設計すること:

- 並行処理・状態遷移・ライフサイクル管理を含む修正 → `references/concurrency-testing.md` を読む
- モックを使用するテスト → `references/mock-patterns.md` を読む
- DB等の外部依存を含むテスト → `references/testcontainers-patterns.md` を読む

リファレンスに記載されたテストパターンが該当するか判断し、該当するパターンをテスト設計に適用すること。「参照」ではなく「読み込んで適用」が必須。

## ECC 由来: skills/golang-testing/SKILL.md

> ECC base commit `4e66b2882da9afb9747468b08a253ca2f09c85f3` の `skills/golang-testing/SKILL.md` を検証したが、本 skill の構造（`references/` に詳細を委譲する索引型 + プロジェクト固有規約 chi/GORM/testify 優先）と異なるため統合せず、**全 H2 を conflicts として記録**。
>
> ECC `golang-testing` は idiomatic Go testing の汎用解説（720 行）:
>
> - **重複領域** (既存と重複、既存優先): Table-Driven Tests / Mocking with Interfaces / TDD Workflow for Go
>   - 既存: §テーブル駆動テストパターン, §モック作成パターン, references/mock-patterns.md, `tdd` skill
> - **既存になし** (将来取り込み余地あり): Subtests and Sub-benchmarks / Test Helpers / Golden Files / Benchmarks / Fuzzing / HTTP Handler Testing / Test Coverage / Testing Commands / Integration with CI/CD
>   - 必要に応じて ECC 原文を `references/ecc-golang-testing.md` として配置するか、特定章を抜粋して既存 reference に追記する形で将来取り込む（本 spec のスコープ外）
> - **TDD は別 skill** (`tdd` skill) に責務を委譲しているため、TDD 関連は本 skill に統合しない方針

## /ECC 由来: skills/golang-testing/SKILL.md
