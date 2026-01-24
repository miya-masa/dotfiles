# Goコーディング規約とベストプラクティス

このリファレンスは、Goのコーディング規約とベストプラクティスを提供します。

## 命名規則

### パッケージ名

```go
// 良い例 - 小文字、短く、簡潔
package user
package httputil
package stringutil

// 悪い例
package UserPackage
package http_util
package myAwesomePackage
```

### 変数名

```go
// 良い例 - キャメルケース
var userCount int
var maxRetryCount int
var httpClient *http.Client

// ループ変数は短く
for i := 0; i < 10; i++ {
    // ...
}

for idx, val := range items {
    // ...
}

// レシーバは1-2文字
func (u *User) GetName() string {
    return u.Name
}

func (uc *UserController) HandleCreate(w http.ResponseWriter, r *http.Request) {
    // ...
}
```

### 定数

```go
// 良い例
const MaxRetryCount = 3
const DefaultTimeout = 30 * time.Second

// 列挙型の定数
const (
    StatusActive   = "active"
    StatusInactive = "inactive"
    StatusPending  = "pending"
)

// iota を使用した列挙
const (
    RoleUser = iota
    RoleAdmin
    RoleSuperAdmin
)
```

### 関数名

```go
// 良い例 - キャメルケース、動詞で開始
func getUserByID(id int64) (*User, error)
func validateEmail(email string) bool
func calculateTotal(items []Item) float64

// エクスポートされる関数は大文字で開始
func NewUser(name, email string) *User
func GetUserByID(id int64) (*User, error)
```

### インターフェース名

```go
// 単一メソッドのインターフェースは -er サフィックス
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Stringer interface {
    String() string
}

// カスタムインターフェース
type UserRepository interface {
    Create(user *User) error
    GetByID(id int64) (*User, error)
    Update(user *User) error
    Delete(id int64) error
}
```

## コード構造

### パッケージの構成

```
project/
├── cmd/
│   └── api/
│       └── main.go
├── internal/
│   ├── domain/
│   │   └── user/
│   │       ├── user.go        # モデル定義
│   │       ├── repository.go  # リポジトリインターフェース
│   │       └── service.go     # ビジネスロジック
│   ├── infrastructure/
│   │   ├── database/
│   │   │   └── user_repository.go  # リポジトリ実装
│   │   └── http/
│   │       └── handler/
│   │           └── user_handler.go  # HTTPハンドラー
│   └── config/
│       └── config.go
├── pkg/
│   └── logger/
│       └── logger.go
└── go.mod
```

### ファイルの構成

```go
// 1. パッケージ宣言
package user

// 2. インポート（標準ライブラリ → 外部ライブラリ → 内部パッケージ）
import (
    "context"
    "fmt"
    "time"

    "github.com/go-chi/chi/v5"
    "gorm.io/gorm"

    "your-project/internal/domain/user"
    "your-project/pkg/logger"
)

// 3. 定数
const (
    MaxPageSize = 100
    DefaultPageSize = 20
)

// 4. 変数
var (
    ErrUserNotFound = errors.New("user not found")
)

// 5. 型定義
type User struct {
    ID    int64
    Name  string
    Email string
}

// 6. コンストラクタ
func NewUser(name, email string) *User {
    return &User{
        Name:  name,
        Email: email,
    }
}

// 7. メソッド
func (u *User) Validate() error {
    // ...
}

// 8. 関数
func GetUserByID(id int64) (*User, error) {
    // ...
}
```

## 関数とメソッド

### 関数の長さ

```go
// 良い例 - 関数は短く、単一の責任を持つ
func createUser(name, email string) (*User, error) {
    if err := validateUserInput(name, email); err != nil {
        return nil, err
    }

    user := &User{Name: name, Email: email}

    if err := saveUser(user); err != nil {
        return nil, err
    }

    return user, nil
}

func validateUserInput(name, email string) error {
    if name == "" {
        return errors.New("name is required")
    }
    if email == "" {
        return errors.New("email is required")
    }
    return nil
}

func saveUser(user *User) error {
    return db.Create(user).Error
}
```

### 引数の数

```go
// 悪い例 - 引数が多すぎる
func createUser(name, email, phone, address, city, country, zipCode string, age int) error {
    // ...
}

// 良い例 - 構造体を使用
type CreateUserRequest struct {
    Name     string
    Email    string
    Phone    string
    Address  string
    City     string
    Country  string
    ZipCode  string
    Age      int
}

func createUser(req CreateUserRequest) error {
    // ...
}
```

### 戻り値

```go
// 良い例 - エラーは最後の戻り値
func getUser(id int64) (*User, error) {
    // ...
}

// 複数の戻り値を返す場合
func getUserWithStats(id int64) (*User, *Stats, error) {
    // ...
}

// 名前付き戻り値（シンプルな関数で使用）
func divide(a, b float64) (result float64, err error) {
    if b == 0 {
        err = errors.New("division by zero")
        return
    }
    result = a / b
    return
}
```

## コメント

### パッケージコメント

```go
// Package user provides user domain models and business logic.
// It includes user management, authentication, and profile operations.
package user
```

### 関数コメント

```go
// GetUserByID retrieves a user by ID from the database.
// Returns ErrUserNotFound if the user does not exist.
func GetUserByID(id int64) (*User, error) {
    // ...
}

// CreateUser creates a new user with the given information.
// It validates the input, checks for duplicates, and saves to the database.
// Returns the created user or an error if the operation fails.
func CreateUser(name, email string) (*User, error) {
    // ...
}
```

### 型コメント

```go
// User represents a user in the system.
// It contains basic user information and authentication details.
type User struct {
    ID        int64     // Unique identifier
    Name      string    // Full name
    Email     string    // Email address (unique)
    CreatedAt time.Time // Account creation timestamp
}
```

### コード内コメント

```go
func processPayment(order *Order) error {
    // 在庫確認
    if !checkInventory(order) {
        return errors.New("insufficient inventory")
    }

    // 支払い処理
    // TODO: エラーハンドリングを改善
    payment, err := chargePayment(order)
    if err != nil {
        return err
    }

    // 注文ステータス更新
    order.Status = "paid"
    order.PaymentID = payment.ID

    return nil
}
```

## エラーハンドリング

### エラーチェック

```go
// 良い例
file, err := os.Open("file.txt")
if err != nil {
    return fmt.Errorf("failed to open file: %w", err)
}
defer file.Close()

// 悪い例 - エラーを無視
file, _ := os.Open("file.txt")
```

### エラーメッセージ

```go
// 良い例 - 小文字で開始、末尾に句読点なし
return errors.New("failed to connect to database")
return fmt.Errorf("invalid user ID: %d", id)

// 悪い例
return errors.New("Failed to connect to database.")
return errors.New("INVALID USER ID")
```

## 並行処理

### Goroutineの使用

```go
// 良い例
func processItems(items []Item) error {
    var wg sync.WaitGroup
    errChan := make(chan error, len(items))

    for _, item := range items {
        wg.Add(1)
        go func(item Item) {
            defer wg.Done()
            if err := processItem(item); err != nil {
                errChan <- err
            }
        }(item)
    }

    wg.Wait()
    close(errChan)

    // エラーチェック
    for err := range errChan {
        if err != nil {
            return err
        }
    }

    return nil
}
```

### チャネルの使用

```go
// 良い例 - バッファサイズを適切に設定
results := make(chan Result, 10)

// 送信専用チャネル
func producer(ch chan<- int) {
    for i := 0; i < 10; i++ {
        ch <- i
    }
    close(ch)
}

// 受信専用チャネル
func consumer(ch <-chan int) {
    for val := range ch {
        fmt.Println(val)
    }
}
```

## ベストプラクティス

### 1. インターフェースは小さく保つ

```go
// 良い例
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// 必要に応じて組み合わせる
type ReadWriter interface {
    Reader
    Writer
}
```

### 2. 依存性注入を使用

```go
// 良い例
type UserService struct {
    repo   UserRepository
    logger Logger
}

func NewUserService(repo UserRepository, logger Logger) *UserService {
    return &UserService{
        repo:   repo,
        logger: logger,
    }
}
```

### 3. コンテキストを活用

```go
func getUser(ctx context.Context, id int64) (*User, error) {
    // タイムアウトチェック
    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    default:
    }

    // データベースクエリにコンテキストを渡す
    var user User
    err := db.WithContext(ctx).First(&user, id).Error
    return &user, err
}
```

### 4. deferを適切に使用

```go
func processFile(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close() // 必ずクローズされることを保証

    // ファイル処理...
    return nil
}
```

### 5. ゼロ値を活用

```go
// 良い例 - ゼロ値で有効な構造体
type Config struct {
    Host    string // デフォルトは ""
    Port    int    // デフォルトは 0
    Timeout time.Duration // デフォルトは 0
}

// 使用側
config := Config{} // ゼロ値で初期化
if config.Host == "" {
    config.Host = "localhost"
}
```

### 6. テーブル駆動テストを使用

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name string
        a, b int
        want int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -2, -3, -5},
        {"mixed signs", -2, 3, 1},
        {"zero", 0, 0, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := add(tt.a, tt.b)
            if got != tt.want {
                t.Errorf("add(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.want)
            }
        })
    }
}
```

### 7. 早期リターンを使用

```go
// 良い例
func processUser(user *User) error {
    if user == nil {
        return errors.New("user is nil")
    }

    if user.Email == "" {
        return errors.New("email is required")
    }

    // 正常処理
    return saveUser(user)
}

// 悪い例 - ネストが深い
func processUser(user *User) error {
    if user != nil {
        if user.Email != "" {
            // 正常処理
            return saveUser(user)
        } else {
            return errors.New("email is required")
        }
    }
    return errors.New("user is nil")
}
```

## フォーマット

### gofmtとgoimports

```bash
# コードのフォーマット
gofmt -w .

# インポートの整理とフォーマット
goimports -w .
```

### 行の長さ

- 行の長さは一般的に80-120文字以内を推奨
- 読みやすさを優先し、必要に応じて改行

```go
// 良い例
user, err := userService.GetUserWithProfile(
    ctx,
    userID,
    includeDeleted,
    withRelations,
)
```

## まとめ

1. **命名規則**: キャメルケース、短く明確な名前を使用
2. **コード構造**: 関数は短く、単一責任の原則を守る
3. **エラーハンドリング**: すべてのエラーを適切に処理
4. **コメント**: エクスポートされる要素には必ずコメントを記述
5. **並行処理**: Goroutineとチャネルを適切に使用
6. **テスト**: テーブル駆動テストで網羅的にテスト
7. **フォーマット**: gofmtとgoimportsを使用してコードを整形
8. **早期リターン**: ネストを浅く保つ
