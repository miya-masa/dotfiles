# Goのエラーハンドリングパターン

このリファレンスは、Goにおけるエラーハンドリングのベストプラクティスとパターンを提供します。

## 基本的なエラーハンドリング

### エラーの返却

```go
func divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("division by zero")
	}
	return a / b, nil
}

// 使用例
func main() {
	result, err := divide(10, 0)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(result)
}
```

### fmt.Errorfを使用したエラーメッセージのフォーマット

```go
func getUser(userID int64) (*User, error) {
	user, err := db.GetUser(userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user %d: %w", userID, err)
	}
	return user, nil
}
```

## カスタムエラー型

### シンプルなカスタムエラー

```go
type NotFoundError struct {
	Resource string
	ID       int64
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s not found: %d", e.Resource, e.ID)
}

func getUser(userID int64) (*User, error) {
	user, err := db.GetUser(userID)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, &NotFoundError{Resource: "User", ID: userID}
		}
		return nil, err
	}
	return user, nil
}
```

### 詳細情報を持つカスタムエラー

```go
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation error on field '%s': %s", e.Field, e.Message)
}

type ValidationErrors []ValidationError

func (e ValidationErrors) Error() string {
	var msgs []string
	for _, err := range e {
		msgs = append(msgs, err.Error())
	}
	return strings.Join(msgs, "; ")
}

func validateUser(user *User) error {
	var errs ValidationErrors

	if user.Name == "" {
		errs = append(errs, ValidationError{Field: "name", Message: "name is required"})
	}

	if user.Email == "" {
		errs = append(errs, ValidationError{Field: "email", Message: "email is required"})
	} else if !isValidEmail(user.Email) {
		errs = append(errs, ValidationError{Field: "email", Message: "invalid email format"})
	}

	if len(errs) > 0 {
		return errs
	}

	return nil
}
```

## センチネルエラー

### 定義と使用

```go
var (
	ErrUserNotFound     = errors.New("user not found")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrUnauthorized     = errors.New("unauthorized")
	ErrForbidden        = errors.New("forbidden")
)

func authenticate(email, password string) (*User, error) {
	user, err := getUserByEmail(email)
	if err != nil {
		return nil, ErrUserNotFound
	}

	if !checkPassword(user, password) {
		return nil, ErrInvalidCredentials
	}

	return user, nil
}

// 使用側
user, err := authenticate(email, password)
if err != nil {
	if errors.Is(err, ErrInvalidCredentials) {
		// 無効な認証情報の処理
		return
	}
	// その他のエラー処理
}
```

## エラーのラッピングとアンラッピング

### エラーのラッピング（%w）

```go
func processOrder(orderID int64) error {
	order, err := getOrder(orderID)
	if err != nil {
		return fmt.Errorf("failed to process order: %w", err)
	}

	if err := validateOrder(order); err != nil {
		return fmt.Errorf("order validation failed: %w", err)
	}

	if err := saveOrder(order); err != nil {
		return fmt.Errorf("failed to save order: %w", err)
	}

	return nil
}
```

### errors.Is による比較

```go
err := processOrder(123)
if err != nil {
	if errors.Is(err, ErrUserNotFound) {
		// ユーザーが見つからない場合の処理
	} else if errors.Is(err, gorm.ErrRecordNotFound) {
		// レコードが見つからない場合の処理
	} else {
		// その他のエラー処理
	}
}
```

### errors.As による型アサーション

```go
err := validateUser(user)
if err != nil {
	var validationErrs ValidationErrors
	if errors.As(err, &validationErrs) {
		// バリデーションエラーの詳細を処理
		for _, e := range validationErrs {
			log.Printf("Field: %s, Error: %s", e.Field, e.Message)
		}
		return
	}

	// その他のエラー処理
}
```

## HTTPハンドラーでのエラーハンドリング

### エラーレスポンスの標準化

```go
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
	Code    string `json:"code,omitempty"`
}

func respondError(w http.ResponseWriter, status int, err error) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	resp := ErrorResponse{
		Error: err.Error(),
	}

	json.NewEncoder(w).Encode(resp)
}

func respondDetailedError(w http.ResponseWriter, status int, code, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	resp := ErrorResponse{
		Error:   http.StatusText(status),
		Message: message,
		Code:    code,
	}

	json.NewEncoder(w).Encode(resp)
}
```

### エラータイプに応じたHTTPステータスコード

```go
func handleGetUser(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.ParseInt(chi.URLParam(r, "userID"), 10, 64)
	if err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	user, err := getUser(userID)
	if err != nil {
		// エラータイプに応じて適切なステータスコードを返す
		var notFoundErr *NotFoundError
		if errors.As(err, &notFoundErr) {
			respondError(w, http.StatusNotFound, err)
			return
		}

		if errors.Is(err, ErrUnauthorized) {
			respondError(w, http.StatusUnauthorized, err)
			return
		}

		if errors.Is(err, ErrForbidden) {
			respondError(w, http.StatusForbidden, err)
			return
		}

		// その他のエラーは500
		logger.Error("Internal error", "error", err)
		respondError(w, http.StatusInternalServerError, errors.New("internal server error"))
		return
	}

	respondJSON(w, http.StatusOK, user)
}
```

### バリデーションエラーの処理

```go
func handleCreateUser(w http.ResponseWriter, r *http.Request) {
	var req CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	// バリデーション
	if err := validateCreateUserRequest(req); err != nil {
		var validationErrs ValidationErrors
		if errors.As(err, &validationErrs) {
			// バリデーションエラーの詳細をレスポンス
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]interface{}{
				"error":  "validation failed",
				"details": validationErrs,
			})
			return
		}

		respondError(w, http.StatusBadRequest, err)
		return
	}

	// ユーザー作成処理...
}
```

## ロギングとエラー

### エラーのロギング

```go
func processPayment(orderID int64) error {
	order, err := getOrder(orderID)
	if err != nil {
		logger.Error("Failed to get order",
			"orderID", orderID,
			"error", err,
		)
		return fmt.Errorf("failed to get order: %w", err)
	}

	payment, err := chargePayment(order)
	if err != nil {
		logger.Error("Payment charge failed",
			"orderID", orderID,
			"amount", order.Amount,
			"error", err,
		)
		return fmt.Errorf("payment charge failed: %w", err)
	}

	logger.Info("Payment processed successfully",
		"orderID", orderID,
		"paymentID", payment.ID,
	)

	return nil
}
```

### エラーレベルの使い分け

```go
func handleRequest(w http.ResponseWriter, r *http.Request) {
	user, err := authenticate(r)
	if err != nil {
		if errors.Is(err, ErrInvalidCredentials) {
			// 想定内のエラーはWarnレベル
			logger.Warn("Authentication failed",
				"ip", r.RemoteAddr,
				"error", err,
			)
			respondError(w, http.StatusUnauthorized, err)
			return
		}

		// システムエラーはErrorレベル
		logger.Error("Authentication system error",
			"error", err,
		)
		respondError(w, http.StatusInternalServerError, errors.New("internal server error"))
		return
	}

	// 正常処理
}
```

## パニックとリカバリー

### パニックの使用（推奨されない）

```go
// パニックは基本的に避けるべき
// どうしても使用する場合は、プログラムが継続不可能な状況のみ
func mustLoadConfig() *Config {
	config, err := loadConfig()
	if err != nil {
		panic(fmt.Sprintf("failed to load config: %v", err))
	}
	return config
}
```

### リカバリー（ミドルウェアでの使用）

```go
func RecovererMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rvr := recover(); rvr != nil {
				// スタックトレースをログに記録
				logger.Error("Panic recovered",
					"error", rvr,
					"stack", string(debug.Stack()),
				)

				http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			}
		}()

		next.ServeHTTP(w, r)
	})
}
```

## エラーハンドリングのベストプラクティス

### 1. エラーは無視しない

```go
// 悪い例
file, _ := os.Open("file.txt")

// 良い例
file, err := os.Open("file.txt")
if err != nil {
	return fmt.Errorf("failed to open file: %w", err)
}
defer file.Close()
```

### 2. エラーは一度だけハンドル

```go
// 悪い例 - エラーをログに記録して返す（呼び出し側で再度ログ記録される）
func getUser(userID int64) (*User, error) {
	user, err := db.GetUser(userID)
	if err != nil {
		logger.Error("Failed to get user", "error", err) // ここでログ
		return nil, err // さらに返す
	}
	return user, nil
}

// 良い例 - エラーを返すのみ（呼び出し側でハンドル）
func getUser(userID int64) (*User, error) {
	user, err := db.GetUser(userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user %d: %w", userID, err)
	}
	return user, nil
}

// 呼び出し側でログとハンドル
func handleGetUser(w http.ResponseWriter, r *http.Request) {
	user, err := getUser(userID)
	if err != nil {
		logger.Error("Get user failed", "error", err)
		respondError(w, http.StatusInternalServerError, err)
		return
	}
	// ...
}
```

### 3. コンテキストを追加してエラーをラップ

```go
func processOrder(orderID int64) error {
	order, err := getOrder(orderID)
	if err != nil {
		// コンテキスト情報を追加
		return fmt.Errorf("failed to process order %d: %w", orderID, err)
	}

	// ...
	return nil
}
```

### 4. センチネルエラーを適切に使用

```go
var (
	// パッケージレベルでエラーを定義
	ErrNotFound = errors.New("not found")
	ErrInvalid  = errors.New("invalid input")
)

func findUser(id int64) (*User, error) {
	// ...
	if user == nil {
		return nil, ErrNotFound
	}
	return user, nil
}
```

### 5. エラーメッセージは小文字で開始

```go
// 良い例
return errors.New("failed to connect to database")

// 悪い例
return errors.New("Failed to connect to database")
```

### 6. 適切なエラータイプを選択

```go
// シンプルなエラー
return errors.New("something went wrong")

// フォーマット付きエラー
return fmt.Errorf("invalid user ID: %d", userID)

// ラップされたエラー
return fmt.Errorf("failed to save user: %w", err)

// カスタムエラー型
return &ValidationError{Field: "email", Message: "invalid format"}

// センチネルエラー
return ErrNotFound
```

## まとめ

1. **エラーは明示的に処理**: すべてのエラーを適切にハンドルする
2. **コンテキストを追加**: エラーをラップして情報を追加
3. **適切なエラータイプ**: センチネルエラー、カスタムエラー型を使い分ける
4. **一貫性**: プロジェクト全体で統一されたエラーハンドリングパターンを使用
5. **ロギング**: エラーは適切なレベルでログに記録
6. **HTTPステータス**: エラータイプに応じた適切なHTTPステータスコードを返す
7. **ユーザーフレンドリー**: エンドユーザーには適切なエラーメッセージを表示
8. **セキュリティ**: 内部エラーの詳細を外部に漏らさない
