# Goテストにおけるモックパターン

このリファレンスは、Goテストでモックを使用するパターンを提供します。

## mockery + testify/mock

mockery は testify/mock と組み合わせて使用するモック生成ツール。インターフェースから自動的にモックコードを生成する。

### mockery のインストール

```bash
go install github.com/vektra/mockery/v2@latest
```

### mockery の設定（.mockery.yaml）

プロジェクトルートに `.mockery.yaml` を作成:

```yaml
with-expecter: true
packages:
  your-project/internal/domain/user:
    interfaces:
      Repository:
        config:
          dir: "mocks"
          outpkg: "mocks"
          filename: "mock_user_repository.go"
  your-project/internal/domain/order:
    interfaces:
      Service:
        config:
          dir: "mocks"
          outpkg: "mocks"
          filename: "mock_order_service.go"
```

### モックの生成

```bash
# 設定ファイルに基づいてモック生成
mockery

# 特定のインターフェースのみ生成
mockery --name=Repository --dir=./internal/domain/user --output=./mocks --outpkg=mocks

# すべてのインターフェースを生成
mockery --all --output=./mocks --outpkg=mocks
```

### 基本的なモック使用

```go
package user_test

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    "your-project/internal/domain/user"
    "your-project/mocks"
)

func TestUserService_GetUser(t *testing.T) {
    tests := []struct {
        name      string
        userID    int64
        mockSetup func(*mocks.MockRepository)
        want      *user.User
        wantErr   bool
    }{
        {
            name:   "success: user found",
            userID: 1,
            mockSetup: func(m *mocks.MockRepository) {
                m.EXPECT().
                    GetByID(mock.Anything, int64(1)).
                    Return(&user.User{ID: 1, Name: "Test User"}, nil).
                    Once()
            },
            want:    &user.User{ID: 1, Name: "Test User"},
            wantErr: false,
        },
        {
            name:   "error: user not found",
            userID: 999,
            mockSetup: func(m *mocks.MockRepository) {
                m.EXPECT().
                    GetByID(mock.Anything, int64(999)).
                    Return(nil, user.ErrNotFound).
                    Once()
            },
            want:    nil,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // モックの作成（t を渡すと自動でアサーション検証）
            mockRepo := mocks.NewMockRepository(t)
            tt.mockSetup(mockRepo)

            // テスト対象の作成
            service := user.NewService(mockRepo)

            // テスト実行
            got, err := service.GetUser(context.Background(), tt.userID)

            // アサーション
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

### EXPECT() メソッドチェーン

mockery の `with-expecter: true` 設定で生成されるメソッド:

```go
// 基本的な期待値設定
mockRepo.EXPECT().
    GetByID(mock.Anything, int64(1)).
    Return(&user.User{ID: 1}, nil)

// 呼び出し回数の指定
mockRepo.EXPECT().
    GetByID(mock.Anything, mock.AnythingOfType("int64")).
    Return(&user.User{ID: 1}, nil).
    Once()           // 1回だけ
    // Times(2)      // 2回
    // Maybe()       // 0回以上

// 引数のマッチング
mockRepo.EXPECT().
    Create(mock.Anything, mock.MatchedBy(func(u *user.User) bool {
        return u.Name != "" && u.Email != ""
    })).
    Return(nil).
    Once()

// 順序の指定（InOrder）
call1 := mockRepo.EXPECT().GetByID(mock.Anything, int64(1)).Return(&user.User{ID: 1}, nil)
call2 := mockRepo.EXPECT().Update(mock.Anything, mock.Anything).Return(nil)
call2.NotBefore(call1)  // call1 の後に call2 が呼ばれることを期待
```

### mock.MatchedBy による柔軟なマッチング

```go
func TestUserService_CreateUser(t *testing.T) {
    mockRepo := mocks.NewMockRepository(t)

    // 引数の条件を柔軟に指定
    mockRepo.EXPECT().
        Create(
            mock.Anything,
            mock.MatchedBy(func(u *user.User) bool {
                return u.Name == "Test" &&
                    u.Email == "test@example.com" &&
                    !u.CreatedAt.IsZero()
            }),
        ).
        Return(nil).
        Once()

    service := user.NewService(mockRepo)
    err := service.CreateUser(context.Background(), "Test", "test@example.com")

    assert.NoError(t, err)
}
```

### Run() でカスタムロジック実行

```go
func TestUserService_UpdateUser(t *testing.T) {
    mockRepo := mocks.NewMockRepository(t)

    // Run() で呼び出し時にカスタムロジックを実行
    mockRepo.EXPECT().
        Update(mock.Anything, mock.Anything).
        Run(func(ctx context.Context, u *user.User) {
            // 引数の検証や副作用のシミュレーション
            assert.Equal(t, int64(1), u.ID)
            u.UpdatedAt = time.Now()
        }).
        Return(nil).
        Once()

    service := user.NewService(mockRepo)
    err := service.UpdateUser(context.Background(), &user.User{ID: 1, Name: "Updated"})

    assert.NoError(t, err)
}
```

### 複数のモックを使用

```go
func TestOrderService_PlaceOrder(t *testing.T) {
    mockUserRepo := mocks.NewMockUserRepository(t)
    mockOrderRepo := mocks.NewMockOrderRepository(t)
    mockPaymentService := mocks.NewMockPaymentService(t)

    // 各モックの期待値を設定
    mockUserRepo.EXPECT().
        GetByID(mock.Anything, int64(1)).
        Return(&user.User{ID: 1, Name: "Test"}, nil).
        Once()

    mockPaymentService.EXPECT().
        Charge(mock.Anything, mock.Anything).
        Return(&payment.Result{TransactionID: "tx123"}, nil).
        Once()

    mockOrderRepo.EXPECT().
        Create(mock.Anything, mock.Anything).
        Return(nil).
        Once()

    // テスト対象の作成
    service := order.NewService(mockUserRepo, mockOrderRepo, mockPaymentService)

    // テスト実行
    result, err := service.PlaceOrder(context.Background(), 1, []order.Item{
        {ProductID: 1, Quantity: 2},
    })

    require.NoError(t, err)
    assert.NotEmpty(t, result.OrderID)
}
```

## httptest を使用した HTTP テスト

### HTTPハンドラーのテスト

```go
package handler_test

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/go-chi/chi/v5"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    "your-project/internal/handler"
    "your-project/mocks"
)

func TestUserHandler_Create(t *testing.T) {
    tests := []struct {
        name           string
        requestBody    interface{}
        mockSetup      func(*mocks.MockUserService)
        wantStatusCode int
        wantBody       map[string]interface{}
    }{
        {
            name: "success: create user",
            requestBody: map[string]string{
                "name":  "Test User",
                "email": "test@example.com",
            },
            mockSetup: func(m *mocks.MockUserService) {
                m.EXPECT().
                    CreateUser(mock.Anything, "Test User", "test@example.com").
                    Return(&user.User{ID: 1, Name: "Test User", Email: "test@example.com"}, nil).
                    Once()
            },
            wantStatusCode: http.StatusCreated,
            wantBody: map[string]interface{}{
                "id":    float64(1),
                "name":  "Test User",
                "email": "test@example.com",
            },
        },
        {
            name: "error: invalid request body",
            requestBody: map[string]string{
                "name": "",  // 空の名前
            },
            mockSetup:      func(m *mocks.MockUserService) {},
            wantStatusCode: http.StatusBadRequest,
            wantBody: map[string]interface{}{
                "error": "name is required",
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // モックのセットアップ
            mockService := mocks.NewMockUserService(t)
            tt.mockSetup(mockService)

            // ハンドラーの作成
            h := handler.NewUserHandler(mockService)

            // リクエストの作成
            body, _ := json.Marshal(tt.requestBody)
            req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(body))
            req.Header.Set("Content-Type", "application/json")

            // レスポンスレコーダーの作成
            rec := httptest.NewRecorder()

            // ハンドラーの実行
            h.Create(rec, req)

            // アサーション
            assert.Equal(t, tt.wantStatusCode, rec.Code)

            var gotBody map[string]interface{}
            err := json.Unmarshal(rec.Body.Bytes(), &gotBody)
            require.NoError(t, err)
            assert.Equal(t, tt.wantBody, gotBody)
        })
    }
}
```

### chi ルーターを含むテスト

```go
func TestUserHandler_Get(t *testing.T) {
    tests := []struct {
        name           string
        userID         string
        mockSetup      func(*mocks.MockUserService)
        wantStatusCode int
    }{
        {
            name:   "success: get user",
            userID: "1",
            mockSetup: func(m *mocks.MockUserService) {
                m.EXPECT().
                    GetUser(mock.Anything, int64(1)).
                    Return(&user.User{ID: 1, Name: "Test"}, nil).
                    Once()
            },
            wantStatusCode: http.StatusOK,
        },
        {
            name:   "error: user not found",
            userID: "999",
            mockSetup: func(m *mocks.MockUserService) {
                m.EXPECT().
                    GetUser(mock.Anything, int64(999)).
                    Return(nil, user.ErrNotFound).
                    Once()
            },
            wantStatusCode: http.StatusNotFound,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockService := mocks.NewMockUserService(t)
            tt.mockSetup(mockService)

            h := handler.NewUserHandler(mockService)

            // chi ルーターをセットアップ
            r := chi.NewRouter()
            r.Get("/users/{userID}", h.Get)

            // リクエストの作成
            req := httptest.NewRequest(http.MethodGet, "/users/"+tt.userID, nil)
            rec := httptest.NewRecorder()

            // ルーター経由でハンドラーを実行
            r.ServeHTTP(rec, req)

            assert.Equal(t, tt.wantStatusCode, rec.Code)
        })
    }
}
```

### 外部APIのモック（httptest.Server）

```go
func TestExternalAPIClient_GetData(t *testing.T) {
    tests := []struct {
        name           string
        serverResponse string
        serverStatus   int
        want           *Data
        wantErr        bool
    }{
        {
            name:           "success: get data",
            serverResponse: `{"id": 1, "value": "test"}`,
            serverStatus:   http.StatusOK,
            want:           &Data{ID: 1, Value: "test"},
            wantErr:        false,
        },
        {
            name:           "error: server error",
            serverResponse: `{"error": "internal error"}`,
            serverStatus:   http.StatusInternalServerError,
            want:           nil,
            wantErr:        true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // モックサーバーの作成
            server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                // リクエストの検証
                assert.Equal(t, http.MethodGet, r.Method)
                assert.Equal(t, "/api/data", r.URL.Path)
                assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

                // レスポンスの返却
                w.WriteHeader(tt.serverStatus)
                w.Write([]byte(tt.serverResponse))
            }))
            defer server.Close()

            // クライアントの作成（モックサーバーのURLを使用）
            client := NewAPIClient(server.URL, "test-token")

            // テスト実行
            got, err := client.GetData(context.Background())

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

### ミドルウェアのテスト

```go
func TestAuthMiddleware(t *testing.T) {
    tests := []struct {
        name           string
        authHeader     string
        mockSetup      func(*mocks.MockAuthService)
        wantStatusCode int
    }{
        {
            name:       "success: valid token",
            authHeader: "Bearer valid-token",
            mockSetup: func(m *mocks.MockAuthService) {
                m.EXPECT().
                    ValidateToken(mock.Anything, "valid-token").
                    Return(&auth.Claims{UserID: 1}, nil).
                    Once()
            },
            wantStatusCode: http.StatusOK,
        },
        {
            name:           "error: missing token",
            authHeader:     "",
            mockSetup:      func(m *mocks.MockAuthService) {},
            wantStatusCode: http.StatusUnauthorized,
        },
        {
            name:       "error: invalid token",
            authHeader: "Bearer invalid-token",
            mockSetup: func(m *mocks.MockAuthService) {
                m.EXPECT().
                    ValidateToken(mock.Anything, "invalid-token").
                    Return(nil, auth.ErrInvalidToken).
                    Once()
            },
            wantStatusCode: http.StatusUnauthorized,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockAuth := mocks.NewMockAuthService(t)
            tt.mockSetup(mockAuth)

            // ダミーハンドラー
            nextHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusOK)
            })

            // ミドルウェアでラップ
            middleware := handler.AuthMiddleware(mockAuth)
            handler := middleware(nextHandler)

            req := httptest.NewRequest(http.MethodGet, "/protected", nil)
            if tt.authHeader != "" {
                req.Header.Set("Authorization", tt.authHeader)
            }
            rec := httptest.NewRecorder()

            handler.ServeHTTP(rec, req)

            assert.Equal(t, tt.wantStatusCode, rec.Code)
        })
    }
}
```

## モック使用のベストプラクティス

1. **mockery の設定ファイルを使用**: プロジェクト全体で一貫したモック生成
2. **`with-expecter: true` を有効化**: EXPECT() メソッドチェーンが使えるようになる
3. **`t` を NewMock に渡す**: テスト終了時に自動でアサーション検証
4. **`mock.Anything` は必要最小限**: 可能な限り具体的な値でマッチング
5. **`mock.MatchedBy` で柔軟なマッチング**: 複雑な条件は関数で検証
6. **呼び出し回数を明示**: `Once()`, `Times(n)` で期待する呼び出し回数を指定
7. **テストケースごとにモックを作成**: モックの状態が他のテストに影響しない
8. **httptest.Server で外部API をモック**: 実際のHTTPリクエストをシミュレート
