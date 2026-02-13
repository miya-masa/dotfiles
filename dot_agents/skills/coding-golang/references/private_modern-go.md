# Go 1.21+ の新機能とモダンなパターン

このリファレンスは、Go 1.21以降で導入された新機能とモダンなコーディングパターンを提供します。

## slog: 構造化ロギング（Go 1.21+）

### 基本的な使用方法

```go
import (
    "log/slog"
    "os"
)

func main() {
    // デフォルトのテキストハンドラー
    logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

    // JSONハンドラー（本番環境向け）
    jsonLogger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

    // ログ出力
    logger.Info("User logged in",
        "userID", 12345,
        "email", "user@example.com",
    )

    // エラーログ
    logger.Error("Failed to process request",
        "error", err,
        "requestID", requestID,
    )
}
```

### ログレベルの設定

```go
import (
    "log/slog"
    "os"
)

func setupLogger(level slog.Level) *slog.Logger {
    opts := &slog.HandlerOptions{
        Level: level,
        // ソースコードの位置を追加
        AddSource: true,
    }

    handler := slog.NewJSONHandler(os.Stdout, opts)
    return slog.New(handler)
}

// 使用例
func main() {
    // 開発環境: Debug レベル
    devLogger := setupLogger(slog.LevelDebug)

    // 本番環境: Info レベル
    prodLogger := setupLogger(slog.LevelInfo)

    devLogger.Debug("Debug message", "key", "value")
    prodLogger.Info("Info message", "key", "value")
}
```

### コンテキスト付きロガー

```go
func processRequest(ctx context.Context, logger *slog.Logger, requestID string) {
    // リクエスト固有の属性を追加したロガー
    reqLogger := logger.With(
        "requestID", requestID,
        "component", "request-processor",
    )

    reqLogger.Info("Processing started")

    // 処理...

    reqLogger.Info("Processing completed", "duration", time.Since(start))
}
```

### slog.Group でのグループ化

```go
logger.Info("Request processed",
    slog.Group("request",
        slog.String("method", "POST"),
        slog.String("path", "/api/users"),
        slog.Int("status", 200),
    ),
    slog.Group("user",
        slog.Int64("id", 12345),
        slog.String("role", "admin"),
    ),
)

// 出力: {"msg":"Request processed","request":{"method":"POST","path":"/api/users","status":200},"user":{"id":12345,"role":"admin"}}
```

### カスタム属性型

```go
// slog.LogValuer インターフェースを実装
type User struct {
    ID    int64
    Name  string
    Email string
}

func (u User) LogValue() slog.Value {
    return slog.GroupValue(
        slog.Int64("id", u.ID),
        slog.String("name", u.Name),
        // emailは機密情報なので省略
    )
}

// 使用例
user := User{ID: 1, Name: "John", Email: "john@example.com"}
logger.Info("User action", "user", user)
// 出力: {"msg":"User action","user":{"id":1,"name":"John"}}
```

## errors.Join: 複数エラーの結合（Go 1.20+）

### 基本的な使用方法

```go
import "errors"

func validateUser(user *User) error {
    var errs []error

    if user.Name == "" {
        errs = append(errs, errors.New("name is required"))
    }

    if user.Email == "" {
        errs = append(errs, errors.New("email is required"))
    }

    if !isValidEmail(user.Email) {
        errs = append(errs, errors.New("invalid email format"))
    }

    if len(errs) > 0 {
        return errors.Join(errs...)
    }

    return nil
}
```

### errors.Is との組み合わせ

```go
var (
    ErrRequired = errors.New("field is required")
    ErrInvalid  = errors.New("invalid format")
)

func validate(value string) error {
    if value == "" {
        return fmt.Errorf("name: %w", ErrRequired)
    }
    if len(value) < 3 {
        return fmt.Errorf("name: %w", ErrInvalid)
    }
    return nil
}

func process() error {
    err1 := validate("")
    err2 := validate("ab")

    combined := errors.Join(err1, err2)

    // errors.Is は結合されたエラーの中を探索
    if errors.Is(combined, ErrRequired) {
        fmt.Println("Contains required error")
    }
    if errors.Is(combined, ErrInvalid) {
        fmt.Println("Contains invalid error")
    }
}
```

### 並行処理でのエラー収集

```go
func processItems(items []Item) error {
    var (
        mu   sync.Mutex
        errs []error
    )

    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1)
        go func(item Item) {
            defer wg.Done()
            if err := processItem(item); err != nil {
                mu.Lock()
                errs = append(errs, fmt.Errorf("item %d: %w", item.ID, err))
                mu.Unlock()
            }
        }(item)
    }

    wg.Wait()

    if len(errs) > 0 {
        return errors.Join(errs...)
    }
    return nil
}
```

## slices パッケージ（Go 1.21+）

### 基本操作

```go
import "slices"

func main() {
    numbers := []int{3, 1, 4, 1, 5, 9, 2, 6}

    // ソート
    slices.Sort(numbers)
    // [1, 1, 2, 3, 4, 5, 6, 9]

    // 逆順ソート
    slices.SortFunc(numbers, func(a, b int) int {
        return b - a  // 降順
    })

    // 要素の検索
    idx, found := slices.BinarySearch(numbers, 5)

    // 要素の存在確認
    contains := slices.Contains(numbers, 5)

    // 最小値・最大値
    min := slices.Min(numbers)
    max := slices.Max(numbers)

    // クローン
    copied := slices.Clone(numbers)

    // 比較
    equal := slices.Equal(numbers, copied)

    // 重複削除（ソート済みスライスに対して）
    slices.Sort(numbers)
    compacted := slices.Compact(numbers)
}
```

### カスタム比較関数

```go
type User struct {
    ID   int64
    Name string
    Age  int
}

func sortUsers(users []User) {
    // 名前でソート
    slices.SortFunc(users, func(a, b User) int {
        return strings.Compare(a.Name, b.Name)
    })

    // 年齢でソート（降順）
    slices.SortFunc(users, func(a, b User) int {
        return b.Age - a.Age
    })

    // 複数条件でソート
    slices.SortFunc(users, func(a, b User) int {
        if a.Age != b.Age {
            return a.Age - b.Age
        }
        return strings.Compare(a.Name, b.Name)
    })
}
```

### Index と IndexFunc

```go
users := []User{
    {ID: 1, Name: "Alice"},
    {ID: 2, Name: "Bob"},
    {ID: 3, Name: "Charlie"},
}

// 条件に一致する最初の要素のインデックスを取得
idx := slices.IndexFunc(users, func(u User) bool {
    return u.Name == "Bob"
})
// idx = 1
```

## maps パッケージ（Go 1.21+）

### 基本操作

```go
import "maps"

func main() {
    original := map[string]int{
        "apple":  1,
        "banana": 2,
        "cherry": 3,
    }

    // クローン
    copied := maps.Clone(original)

    // マップの比較
    equal := maps.Equal(original, copied)

    // キーの取得
    keys := slices.Collect(maps.Keys(original))

    // 値の取得
    values := slices.Collect(maps.Values(original))

    // マップのマージ（dst に src をコピー）
    dst := map[string]int{"date": 4}
    maps.Copy(dst, original)
    // dst = {"date": 4, "apple": 1, "banana": 2, "cherry": 3}

    // 条件に一致する要素を削除
    maps.DeleteFunc(original, func(key string, value int) bool {
        return value < 2
    })
}
```

## clear 組み込み関数（Go 1.21+）

### スライスのクリア

```go
func main() {
    numbers := []int{1, 2, 3, 4, 5}

    // スライスをクリア（長さは維持、要素はゼロ値に）
    clear(numbers)
    // numbers = [0, 0, 0, 0, 0]
    // len(numbers) = 5
}
```

### マップのクリア

```go
func main() {
    data := map[string]int{
        "a": 1,
        "b": 2,
    }

    // マップをクリア（すべてのキーを削除）
    clear(data)
    // data = {}
    // len(data) = 0
}
```

### バッファの再利用パターン

```go
type BufferPool struct {
    buffer []byte
}

func (p *BufferPool) GetBuffer(size int) []byte {
    if cap(p.buffer) < size {
        p.buffer = make([]byte, size)
    } else {
        p.buffer = p.buffer[:size]
        clear(p.buffer)  // ゼロクリア
    }
    return p.buffer
}
```

## max/min 組み込み関数（Go 1.21+）

### 基本的な使用方法

```go
func main() {
    // 整数
    maxInt := max(1, 5, 3)  // 5
    minInt := min(1, 5, 3)  // 1

    // 浮動小数点
    maxFloat := max(1.5, 2.5, 0.5)  // 2.5
    minFloat := min(1.5, 2.5, 0.5)  // 0.5

    // 文字列（辞書順）
    maxStr := max("apple", "banana", "cherry")  // "cherry"
    minStr := min("apple", "banana", "cherry")  // "apple"
}
```

### 実用的な使用例

```go
// ページネーション
func paginate(total, page, pageSize int) (offset, limit int) {
    page = max(1, page)                    // 最小1ページ
    pageSize = max(1, min(100, pageSize))  // 1-100の範囲

    offset = (page - 1) * pageSize
    limit = pageSize

    return offset, limit
}

// タイムアウト設定
func withTimeout(requested, maxAllowed time.Duration) time.Duration {
    return min(requested, maxAllowed)
}

// リトライ回数
func getRetryCount(attempts, maxRetries int) int {
    return min(attempts, maxRetries)
}
```

## for range の変更（Go 1.22+）

### ループ変数のキャプチャ問題の解消

```go
// Go 1.22以降では、各イテレーションで新しい変数が作成される

func main() {
    values := []int{1, 2, 3}
    var funcs []func()

    // Go 1.22+: 正しく動作
    for _, v := range values {
        funcs = append(funcs, func() {
            fmt.Println(v)
        })
    }

    for _, f := range funcs {
        f()
    }
    // 出力: 1, 2, 3（期待通り）

    // Go 1.21以前では: 3, 3, 3 となっていた
}
```

### 整数の範囲ループ（Go 1.22+）

```go
// 0 から n-1 までのループ
for i := range 10 {
    fmt.Println(i)  // 0, 1, 2, ..., 9
}

// 従来の書き方
for i := 0; i < 10; i++ {
    fmt.Println(i)
}
```

## cmp パッケージ（Go 1.21+）

### 比較関数

```go
import "cmp"

func main() {
    // 比較（-1, 0, 1 を返す）
    result := cmp.Compare(5, 3)  // 1 (5 > 3)
    result = cmp.Compare(3, 5)   // -1 (3 < 5)
    result = cmp.Compare(3, 3)   // 0 (3 == 3)

    // Less
    less := cmp.Less(3, 5)  // true

    // Or（最初の非ゼロ値を返す）
    value := cmp.Or(0, 0, 3, 5)  // 3
    value = cmp.Or("", "", "hello")  // "hello"
}
```

### cmp.Or のデフォルト値パターン

```go
func getConfig(custom string) string {
    // カスタム値があればそれを使用、なければデフォルト
    return cmp.Or(custom, os.Getenv("CONFIG"), "default")
}

func getUserName(user *User) string {
    if user == nil {
        return "anonymous"
    }
    return cmp.Or(user.DisplayName, user.Name, "unknown")
}
```

## context パッケージの改善

### context.WithoutCancel（Go 1.21+）

```go
import "context"

func handleRequest(ctx context.Context) {
    // 親のキャンセルを引き継がないコンテキストを作成
    // タイムアウトや値は継承されるが、キャンセルは伝播しない
    bgCtx := context.WithoutCancel(ctx)

    // バックグラウンド処理（リクエストがキャンセルされても継続）
    go func() {
        sendMetrics(bgCtx, metrics)
    }()
}
```

### context.AfterFunc（Go 1.21+）

```go
func processWithCleanup(ctx context.Context) {
    // コンテキストがキャンセルされたときに実行される関数を登録
    stop := context.AfterFunc(ctx, func() {
        fmt.Println("Context cancelled, cleaning up...")
        cleanup()
    })

    // 処理が正常に完了した場合はクリーンアップ関数をキャンセル
    defer stop()

    // メイン処理...
}
```

## sync パッケージの改善

### sync.OnceFunc / sync.OnceValue / sync.OnceValues（Go 1.21+）

```go
import "sync"

// 一度だけ実行される関数
var initialize = sync.OnceFunc(func() {
    fmt.Println("Initializing...")
})

// 一度だけ計算される値
var getConfig = sync.OnceValue(func() *Config {
    return loadConfig()
})

// 複数の戻り値
var loadData = sync.OnceValues(func() ([]byte, error) {
    return os.ReadFile("data.json")
})

func main() {
    initialize()  // "Initializing..."
    initialize()  // 何も出力されない

    config := getConfig()  // 最初の呼び出しで計算
    config = getConfig()   // キャッシュされた値を返す

    data, err := loadData()
}
```

## ベストプラクティス

1. **slog を積極的に活用**: 構造化ログで運用性向上
2. **errors.Join でエラーを集約**: バリデーションや並行処理で有効
3. **slices/maps を使用**: 標準的な操作を簡潔に記述
4. **max/min で境界チェック**: ページネーションやリミット設定に便利
5. **cmp.Or でデフォルト値**: 簡潔なフォールバック処理
6. **Go 1.22+ のループ変数**: ゴルーチンでのキャプチャ問題が解消
7. **sync.OnceValue**: シングルトンパターンの簡潔な実装

