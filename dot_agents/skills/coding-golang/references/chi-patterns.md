# Chi ルーターの使用パターン

このリファレンスは、go-chiを使用したHTTPルーティングの一般的なパターンを提供します。

## 基本的なルーター設定

```go
package main

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func NewRouter() *chi.Mux {
	r := chi.NewRouter()

	// 標準ミドルウェア
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	// ルート定義
	r.Get("/", handleHome)
	r.Get("/health", handleHealth)

	return r
}

func handleHome(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Welcome"))
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}
```

## RESTful APIルーティング

```go
func SetupAPIRoutes(r *chi.Mux) {
	r.Route("/api/v1", func(r chi.Router) {
		// ユーザーリソース
		r.Route("/users", func(r chi.Router) {
			r.Get("/", listUsers)       // GET /api/v1/users
			r.Post("/", createUser)      // POST /api/v1/users

			r.Route("/{userID}", func(r chi.Router) {
				r.Get("/", getUser)       // GET /api/v1/users/{userID}
				r.Put("/", updateUser)    // PUT /api/v1/users/{userID}
				r.Delete("/", deleteUser) // DELETE /api/v1/users/{userID}
			})
		})

		// 記事リソース
		r.Route("/articles", func(r chi.Router) {
			r.Get("/", listArticles)
			r.Post("/", createArticle)

			r.Route("/{articleID}", func(r chi.Router) {
				r.Get("/", getArticle)
				r.Put("/", updateArticle)
				r.Delete("/", deleteArticle)

				// ネストされたリソース
				r.Route("/comments", func(r chi.Router) {
					r.Get("/", listComments)
					r.Post("/", createComment)
				})
			})
		})
	})
}
```

## URLパラメータの取得

```go
func getUser(w http.ResponseWriter, r *http.Request) {
	// URLパラメータの取得
	userID := chi.URLParam(r, "userID")

	// バリデーション
	if userID == "" {
		http.Error(w, "User ID is required", http.StatusBadRequest)
		return
	}

	// 処理...
}

func getComment(w http.ResponseWriter, r *http.Request) {
	// 複数のURLパラメータ
	articleID := chi.URLParam(r, "articleID")
	commentID := chi.URLParam(r, "commentID")

	// 処理...
}
```

## クエリパラメータの取得

```go
func listUsers(w http.ResponseWriter, r *http.Request) {
	// クエリパラメータの取得
	page := r.URL.Query().Get("page")
	limit := r.URL.Query().Get("limit")
	search := r.URL.Query().Get("search")

	// デフォルト値の設定
	if page == "" {
		page = "1"
	}
	if limit == "" {
		limit = "20"
	}

	// 処理...
}
```

## カスタムミドルウェア

### 認証ミドルウェア

```go
func AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := r.Header.Get("Authorization")

		if token == "" {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// トークン検証
		userID, err := validateToken(token)
		if err != nil {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		// コンテキストにユーザーIDを設定
		ctx := context.WithValue(r.Context(), "userID", userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// 使用例
func SetupProtectedRoutes(r *chi.Mux) {
	r.Group(func(r chi.Router) {
		r.Use(AuthMiddleware)

		r.Get("/profile", getProfile)
		r.Put("/profile", updateProfile)
	})
}
```

### ロギングミドルウェア（カスタムロガー使用）

```go
func LoggingMiddleware(logger Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// レスポンスライターをラップして状態コードをキャプチャ
			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

			defer func() {
				logger.Info("HTTP Request",
					"method", r.Method,
					"path", r.URL.Path,
					"status", ww.Status(),
					"duration", time.Since(start),
					"ip", r.RemoteAddr,
				)
			}()

			next.ServeHTTP(ww, r)
		})
	}
}
```

### CORS ミドルウェア

```go
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// プリフライトリクエストの処理
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
```

## コンテキストの使用

```go
type contextKey string

const (
	userIDKey contextKey = "userID"
	roleKey   contextKey = "role"
)

// コンテキストへの値の設定
func SetUserContext(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userID := getUserIDFromToken(r)
		role := getRoleFromToken(r)

		ctx := r.Context()
		ctx = context.WithValue(ctx, userIDKey, userID)
		ctx = context.WithValue(ctx, roleKey, role)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// コンテキストからの値の取得
func getProfile(w http.ResponseWriter, r *http.Request) {
	userID, ok := r.Context().Value(userIDKey).(string)
	if !ok {
		http.Error(w, "User ID not found", http.StatusInternalServerError)
		return
	}

	role, _ := r.Context().Value(roleKey).(string)

	// 処理...
}
```

## グループとサブルーター

```go
func SetupRoutes(r *chi.Mux) {
	// パブリックルート
	r.Group(func(r chi.Router) {
		r.Get("/", handleHome)
		r.Get("/login", handleLogin)
		r.Post("/register", handleRegister)
	})

	// 認証が必要なルート
	r.Group(func(r chi.Router) {
		r.Use(AuthMiddleware)

		r.Get("/dashboard", handleDashboard)
		r.Get("/settings", handleSettings)
	})

	// 管理者専用ルート
	r.Group(func(r chi.Router) {
		r.Use(AuthMiddleware)
		r.Use(AdminMiddleware)

		r.Route("/admin", func(r chi.Router) {
			r.Get("/users", adminListUsers)
			r.Delete("/users/{userID}", adminDeleteUser)
		})
	})
}
```

## エラーハンドリング

```go
// JSONレスポンスヘルパー
func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func respondError(w http.ResponseWriter, status int, message string) {
	respondJSON(w, status, map[string]string{"error": message})
}

// ハンドラーでの使用例
func createUser(w http.ResponseWriter, r *http.Request) {
	var req CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// バリデーション
	if err := validateCreateUserRequest(req); err != nil {
		respondError(w, http.StatusBadRequest, err.Error())
		return
	}

	// ユーザー作成
	user, err := createUserInDB(req)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Failed to create user")
		return
	}

	respondJSON(w, http.StatusCreated, user)
}
```

## リクエストバリデーション

```go
type CreateUserRequest struct {
	Name     string `json:"name"`
	Email    string `json:"email"`
	Password string `json:"password"`
}

func validateCreateUserRequest(req CreateUserRequest) error {
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	if req.Email == "" {
		return fmt.Errorf("email is required")
	}
	if !isValidEmail(req.Email) {
		return fmt.Errorf("invalid email format")
	}
	if len(req.Password) < 8 {
		return fmt.Errorf("password must be at least 8 characters")
	}
	return nil
}

func createUser(w http.ResponseWriter, r *http.Request) {
	var req CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if err := validateCreateUserRequest(req); err != nil {
		respondError(w, http.StatusBadRequest, err.Error())
		return
	}

	// 処理...
}
```

## ファイルアップロード

```go
func uploadFile(w http.ResponseWriter, r *http.Request) {
	// 最大10MBまで
	r.ParseMultipartForm(10 << 20)

	file, handler, err := r.FormFile("file")
	if err != nil {
		respondError(w, http.StatusBadRequest, "Error retrieving file")
		return
	}
	defer file.Close()

	// ファイル名とサイズの取得
	fileName := handler.Filename
	fileSize := handler.Size

	// ファイルの保存
	dst, err := os.Create(filepath.Join("./uploads", fileName))
	if err != nil {
		respondError(w, http.StatusInternalServerError, "Error saving file")
		return
	}
	defer dst.Close()

	if _, err := io.Copy(dst, file); err != nil {
		respondError(w, http.StatusInternalServerError, "Error saving file")
		return
	}

	respondJSON(w, http.StatusOK, map[string]interface{}{
		"filename": fileName,
		"size":     fileSize,
	})
}
```

## タイムアウト設定

```go
func TimeoutMiddleware(timeout time.Duration) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx, cancel := context.WithTimeout(r.Context(), timeout)
			defer cancel()

			done := make(chan struct{})

			go func() {
				next.ServeHTTP(w, r.WithContext(ctx))
				close(done)
			}()

			select {
			case <-done:
				return
			case <-ctx.Done():
				http.Error(w, "Request timeout", http.StatusRequestTimeout)
			}
		})
	}
}

// 使用例
func SetupRoutes(r *chi.Mux) {
	r.Group(func(r chi.Router) {
		r.Use(TimeoutMiddleware(30 * time.Second))
		r.Post("/upload", uploadFile)
	})
}
```

## ベストプラクティス

1. **ミドルウェアの順序**: 重要なミドルウェア（Recoverer、RequestIDなど）を最初に配置
2. **エラーハンドリング**: 一貫したエラーレスポンス形式を使用
3. **バリデーション**: リクエストボディとパラメータを必ずバリデーション
4. **コンテキスト使用**: 認証情報などをコンテキストで伝播
5. **グループ化**: 関連するルートをグループ化して可読性を向上
6. **RESTful設計**: リソースベースのURL設計を採用
7. **タイムアウト**: 長時間実行される可能性のある処理にはタイムアウトを設定
8. **CORS**: フロントエンドとの連携時は適切なCORS設定を実装
