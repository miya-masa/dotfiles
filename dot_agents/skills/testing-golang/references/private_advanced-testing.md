# Goの高度なテストパターン

このリファレンスは、ファズテスト、ベンチマークテスト、並列テストなどの高度なテストパターンを提供します。

## ファズテスト（Go 1.18+）

ファズテストは、ランダムな入力を生成してバグを発見するテスト手法。

### 基本的なファズテスト

```go
package mypackage_test

import (
    "testing"
    "unicode/utf8"
)

func FuzzReverse(f *testing.F) {
    // シードコーパス（初期入力値）の追加
    testcases := []string{"Hello, world", " ", "!12345", "日本語"}
    for _, tc := range testcases {
        f.Add(tc)
    }

    // ファズ関数
    f.Fuzz(func(t *testing.T, orig string) {
        rev := Reverse(orig)
        doubleRev := Reverse(rev)

        // プロパティベースのアサーション
        if orig != doubleRev {
            t.Errorf("Before: %q, after: %q", orig, doubleRev)
        }

        if utf8.ValidString(orig) && !utf8.ValidString(rev) {
            t.Errorf("Reverse produced invalid UTF-8 string %q", rev)
        }
    })
}
```

### 複数引数のファズテスト

```go
func FuzzParseInt(f *testing.F) {
    // 複数の引数を持つシードコーパス
    f.Add("123", 10)
    f.Add("0xFF", 16)
    f.Add("-456", 10)
    f.Add("invalid", 10)

    f.Fuzz(func(t *testing.T, s string, base int) {
        // 無効なベースをスキップ
        if base < 2 || base > 36 {
            t.Skip()
        }

        result, err := ParseInt(s, base)
        if err != nil {
            // エラーが発生した場合はパニックしていないことを確認
            return
        }

        // 結果の検証
        formatted := FormatInt(result, base)
        if formatted != s {
            t.Errorf("ParseInt(%q, %d) = %d, FormatInt = %q", s, base, result, formatted)
        }
    })
}
```

### ファズテストの実行

```bash
# ファズテストを実行（10秒間）
go test -fuzz=FuzzReverse -fuzztime=10s

# 特定のシードで再現
go test -run=FuzzReverse/seed_corpus_file

# 失敗したケースは testdata/fuzz/<FuzzTestName>/ に保存される
```

### 構造体のファズテスト

```go
func FuzzUserValidation(f *testing.F) {
    // バイト列として追加
    f.Add([]byte(`{"name": "test", "email": "test@example.com"}`))
    f.Add([]byte(`{}`))
    f.Add([]byte(`{"name": ""}`))

    f.Fuzz(func(t *testing.T, data []byte) {
        var user User
        err := json.Unmarshal(data, &user)
        if err != nil {
            // 無効なJSONはスキップ
            return
        }

        // Validate がパニックしないことを確認
        _ = user.Validate()
    })
}
```

## ベンチマークテスト

### 基本的なベンチマーク

```go
func BenchmarkFunctionName(b *testing.B) {
    // セットアップ（計測外）
    data := prepareData()

    // タイマーリセット（セットアップ時間を除外）
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        FunctionName(data)
    }
}
```

### メモリアロケーションの計測

```go
func BenchmarkWithAllocs(b *testing.B) {
    b.ReportAllocs() // アロケーション情報を報告

    for i := 0; i < b.N; i++ {
        result := ProcessData(testData)
        _ = result
    }
}
```

### サブベンチマーク

```go
func BenchmarkSliceOperations(b *testing.B) {
    sizes := []int{10, 100, 1000, 10000}

    for _, size := range sizes {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := make([]int, size)
            for i := range data {
                data[i] = i
            }

            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                ProcessSlice(data)
            }
        })
    }
}
```

### 並列ベンチマーク

```go
func BenchmarkParallel(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        // 各Goroutine用のローカル状態
        localData := prepareLocalData()

        for pb.Next() {
            ProcessData(localData)
        }
    })
}
```

### ベンチマークの実行

```bash
# ベンチマーク実行
go test -bench=. -benchmem

# 特定のベンチマークのみ
go test -bench=BenchmarkSliceOperations -benchmem

# CPU プロファイル取得
go test -bench=. -cpuprofile=cpu.prof

# メモリプロファイル取得
go test -bench=. -memprofile=mem.prof

# 結果の比較（benchstat）
go test -bench=. -count=10 > old.txt
# コード変更後
go test -bench=. -count=10 > new.txt
benchstat old.txt new.txt
```

### ベンチマーク結果の読み方

```
BenchmarkFunctionName-8    1000000    1234 ns/op    256 B/op    4 allocs/op
                      │          │         │           │            │
                      │          │         │           │            └── アロケーション回数
                      │          │         │           └── 1回あたりのメモリ使用量
                      │          │         └── 1回あたりの実行時間
                      │          └── 実行回数
                      └── 使用したCPUコア数
```

## 並列テスト

### t.Parallel() の使用

```go
func TestParallel(t *testing.T) {
    tests := []struct {
        name  string
        input int
        want  int
    }{
        {"case1", 1, 2},
        {"case2", 2, 4},
        {"case3", 3, 6},
    }

    for _, tt := range tests {
        tt := tt // Go 1.21以前では必要（ループ変数のキャプチャ）
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // このサブテストを並列実行

            got := Double(tt.input)
            if got != tt.want {
                t.Errorf("Double(%d) = %d, want %d", tt.input, got, tt.want)
            }
        })
    }
}
```

### 共有リソースを持つ並列テスト

```go
func TestParallelWithSharedResource(t *testing.T) {
    // 共有リソースのセットアップ（テスト全体で1回）
    db := setupDatabase(t)

    tests := []struct {
        name   string
        userID int64
    }{
        {"user1", 1},
        {"user2", 2},
        {"user3", 3},
    }

    for _, tt := range tests {
        tt := tt
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()

            // 各テストは独自のデータを使用
            user, err := db.GetUser(tt.userID)
            require.NoError(t, err)
            assert.Equal(t, tt.userID, user.ID)
        })
    }
}
```

### 並列テストでのクリーンアップ

```go
func TestParallelWithCleanup(t *testing.T) {
    tests := []struct {
        name string
    }{
        {"test1"},
        {"test2"},
    }

    for _, tt := range tests {
        tt := tt
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()

            // テスト固有のリソース作成
            resource := createResource(t)

            // t.Cleanup() は並列テストでも安全
            t.Cleanup(func() {
                resource.Close()
            })

            // テスト実行
            useResource(resource)
        })
    }
}
```

## テストヘルパー

### t.Helper() の使用

```go
func assertUserEquals(t *testing.T, expected, actual *User) {
    t.Helper() // エラー時にこの関数ではなく呼び出し元を報告

    if expected.ID != actual.ID {
        t.Errorf("ID mismatch: expected %d, got %d", expected.ID, actual.ID)
    }
    if expected.Name != actual.Name {
        t.Errorf("Name mismatch: expected %s, got %s", expected.Name, actual.Name)
    }
}

func TestUser(t *testing.T) {
    user := GetUser(1)
    expected := &User{ID: 1, Name: "Test"}

    assertUserEquals(t, expected, user) // エラー時はこの行が報告される
}
```

### テストフィクスチャ

```go
func setupTestUser(t *testing.T) (*User, func()) {
    t.Helper()

    user := &User{
        ID:    1,
        Name:  "Test User",
        Email: "test@example.com",
    }

    // データベースに保存など
    err := saveUser(user)
    require.NoError(t, err)

    cleanup := func() {
        deleteUser(user.ID)
    }

    return user, cleanup
}

func TestWithFixture(t *testing.T) {
    user, cleanup := setupTestUser(t)
    defer cleanup()

    // user を使用したテスト
}
```

### t.Cleanup() の活用

```go
func setupDatabase(t *testing.T) *sql.DB {
    t.Helper()

    db, err := sql.Open("postgres", testDSN)
    require.NoError(t, err)

    // テスト終了時に自動クリーンアップ
    t.Cleanup(func() {
        db.Close()
    })

    return db
}

func TestDatabase(t *testing.T) {
    db := setupDatabase(t) // cleanup は自動で呼ばれる

    // db を使用したテスト
}
```

## テストのスキップ

```go
func TestRequiresDocker(t *testing.T) {
    if os.Getenv("DOCKER_HOST") == "" {
        t.Skip("Skipping test: Docker not available")
    }

    // Docker を使用したテスト
}

func TestSlowOperation(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping slow test in short mode")
    }

    // 時間のかかるテスト
}

// 実行: go test -short でスキップ
```

## テストのタグ付け（ビルドタグ）

```go
//go:build integration

package mypackage_test

// このファイルは go test -tags=integration でのみ実行される
func TestIntegration(t *testing.T) {
    // 統合テスト
}
```

```bash
# 統合テストを含めて実行
go test -tags=integration ./...

# 統合テストを除外して実行（デフォルト）
go test ./...
```

## テストカバレッジ

```bash
# カバレッジを計測
go test -cover ./...

# カバレッジプロファイルを出力
go test -coverprofile=coverage.out ./...

# HTML レポートを生成
go tool cover -html=coverage.out -o coverage.html

# 関数ごとのカバレッジ
go tool cover -func=coverage.out
```

## 競合状態の検出

```bash
# Race Detector を有効にしてテスト
go test -race ./...

# ベンチマークでも使用可能
go test -race -bench=. ./...
```

## ベストプラクティス

1. **ファズテスト**: セキュリティに関わるパースや入力処理に適用
2. **ベンチマーク**: パフォーマンスクリティカルなコードに適用
3. **並列テスト**: 独立したテストケースは `t.Parallel()` で高速化
4. **t.Helper()**: カスタムアサーション関数には必ず追加
5. **t.Cleanup()**: リソースの解放は defer より t.Cleanup() を優先
6. **ビルドタグ**: 重いテストは分離して通常のテストを高速に
7. **Race Detector**: CI で常に `-race` を有効化
8. **カバレッジ**: 目安として80%以上を目指す
