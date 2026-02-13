# GoテストにおけるTestcontainersパターン

このリファレンスは、Goユニットテストでtestcontainersを使用する一般的なパターンを提供します。

## 基本的なPostgreSQLコンテナパターン

```go
package mypackage_test

import (
 "context"
 "database/sql"
 "fmt"
 "testing"
 "time"

 "github.com/stretchr/testify/assert"
 "github.com/stretchr/testify/require"
 "github.com/testcontainers/testcontainers-go"
 "github.com/testcontainers/testcontainers-go/wait"
)

func setupPostgresContainer(t *testing.T) (*sql.DB, func()) {
 ctx := context.Background()

 req := testcontainers.ContainerRequest{
  Image:        "postgres:15-alpine",
  ExposedPorts: []string{"5432/tcp"},
  Env: map[string]string{
   "POSTGRES_USER":     "testuser",
   "POSTGRES_PASSWORD": "testpass",
   "POSTGRES_DB":       "testdb",
  },
  WaitingFor: wait.ForLog("database system is ready to accept connections").
   WithOccurrence(2).
   WithStartupTimeout(60 * time.Second),
 }

 container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
  ContainerRequest: req,
  Started:          true,
 })
 require.NoError(t, err)

 host, err := container.Host(ctx)
 require.NoError(t, err)

 port, err := container.MappedPort(ctx, "5432")
 require.NoError(t, err)

 dsn := fmt.Sprintf("host=%s port=%s user=testuser password=testpass dbname=testdb sslmode=disable", host, port.Port())
 db, err := sql.Open("postgres", dsn)
 require.NoError(t, err)

 cleanup := func() {
  db.Close()
  container.Terminate(ctx)
 }

 return db, cleanup
}
```

## MySQLコンテナパターン

```go
func setupMySQLContainer(t *testing.T) (*sql.DB, func()) {
 ctx := context.Background()

 req := testcontainers.ContainerRequest{
  Image:        "mysql:8.0",
  ExposedPorts: []string{"3306/tcp"},
  Env: map[string]string{
   "MYSQL_ROOT_PASSWORD": "rootpass",
   "MYSQL_DATABASE":      "testdb",
   "MYSQL_USER":          "testuser",
   "MYSQL_PASSWORD":      "testpass",
  },
  WaitingFor: wait.ForLog("port: 3306  MySQL Community Server").
   WithStartupTimeout(60 * time.Second),
 }

 container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
  ContainerRequest: req,
  Started:          true,
 })
 require.NoError(t, err)

 host, err := container.Host(ctx)
 require.NoError(t, err)

 port, err := container.MappedPort(ctx, "3306")
 require.NoError(t, err)

 dsn := fmt.Sprintf("testuser:testpass@tcp(%s:%s)/testdb?parseTime=true", host, port.Port())
 db, err := sql.Open("mysql", dsn)
 require.NoError(t, err)

 cleanup := func() {
  db.Close()
  container.Terminate(ctx)
 }

 return db, cleanup
}
```

## Redisコンテナパターン

```go
import (
 "github.com/redis/go-redis/v9"
)

func setupRedisContainer(t *testing.T) (*redis.Client, func()) {
 ctx := context.Background()

 req := testcontainers.ContainerRequest{
  Image:        "redis:7-alpine",
  ExposedPorts: []string{"6379/tcp"},
  WaitingFor:   wait.ForLog("Ready to accept connections"),
 }

 container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
  ContainerRequest: req,
  Started:          true,
 })
 require.NoError(t, err)

 host, err := container.Host(ctx)
 require.NoError(t, err)

 port, err := container.MappedPort(ctx, "6379")
 require.NoError(t, err)

 client := redis.NewClient(&redis.Options{
  Addr: fmt.Sprintf("%s:%s", host, port.Port()),
 })

 cleanup := func() {
  client.Close()
  container.Terminate(ctx)
 }

 return client, cleanup
}
```

## テーブル駆動テストでのコンテナ使用

```go
func TestDatabaseOperations(t *testing.T) {
 db, cleanup := setupPostgresContainer(t)
 defer cleanup()

 // マイグレーションの実行またはスキーマのセットアップ
 _, err := db.Exec(`CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)`)
 require.NoError(t, err)

 tests := []struct {
  name    string
  input   string
  wantErr bool
 }{
  {
   name:    "有効なユーザー",
   input:   "山田太郎",
   wantErr: false,
  },
  {
   name:    "空の名前",
   input:   "",
   wantErr: true,
  },
 }

 for _, tt := range tests {
  t.Run(tt.name, func(t *testing.T) {
   // 各テストケースは同じコンテナを使用
   // 必要に応じてテストケース間でデータをクリーンアップ
   result, err := insertUser(db, tt.input)
   if tt.wantErr {
    assert.Error(t, err)
   } else {
    assert.NoError(t, err)
    assert.NotNil(t, result)
   }
  })
 }
}
```

## 並列テスト実行とコンテナ

```go
func TestParallelDatabaseOperations(t *testing.T) {
 tests := []struct {
  name    string
  input   string
  wantErr bool
 }{
  {
   name:    "テストケース1",
   input:   "データ1",
   wantErr: false,
  },
  {
   name:    "テストケース2",
   input:   "データ2",
   wantErr: false,
  },
 }

 for _, tt := range tests {
  tt := tt // range変数をキャプチャ
  t.Run(tt.name, func(t *testing.T) {
   t.Parallel() // テストを並列実行

   // 各並列テストは独自のコンテナを取得
   db, cleanup := setupPostgresContainer(t)
   defer cleanup()

   // このテスト用のスキーマをセットアップ
   _, err := db.Exec(`CREATE TABLE test_data (id SERIAL PRIMARY KEY, value TEXT)`)
   require.NoError(t, err)

   // テストロジックを実行
   result, err := processData(db, tt.input)
   if tt.wantErr {
    assert.Error(t, err)
   } else {
    assert.NoError(t, err)
    assert.NotNil(t, result)
   }
  })
 }
}
```

## カスタム設定ファイルを使用したコンテナ

```go
func setupPostgresWithCustomConfig(t *testing.T) (*sql.DB, func()) {
 ctx := context.Background()

 req := testcontainers.ContainerRequest{
  Image:        "postgres:15-alpine",
  ExposedPorts: []string{"5432/tcp"},
  Env: map[string]string{
   "POSTGRES_USER":     "testuser",
   "POSTGRES_PASSWORD": "testpass",
   "POSTGRES_DB":       "testdb",
  },
  Files: []testcontainers.ContainerFile{
   {
    HostFilePath:      "./testdata/init.sql",
    ContainerFilePath: "/docker-entrypoint-initdb.d/init.sql",
    FileMode:          0755,
   },
  },
  WaitingFor: wait.ForLog("database system is ready to accept connections").
   WithOccurrence(2),
 }

 container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
  ContainerRequest: req,
  Started:          true,
 })
 require.NoError(t, err)

 // ... 残りのセットアップ
}
```

## ベストプラクティス

1. **常にクリーンアップ関数を使用**: テスト完了後にコンテナが確実に終了するようにする
2. **セットアップにはrequireを使用**: `require.NoError()`を使用してコンテナセットアップで早期に失敗させる
3. **待機戦略**: コンテナの準備完了に適した待機戦略を選択
4. **並列テスト**: テストを並列実行できるか検討（それぞれ独自のコンテナが必要）
5. **コンテナの再利用**: 非並列テストでは、テストケース間で同じコンテナを再利用
6. **スキーマ管理**: コンテナを再利用する場合は、テストケース間でスキーマをリセットまたは再作成
7. **タイムアウト値**: コンテナイメージサイズに基づいて適切な起動タイムアウトを設定
8. **リソースクリーンアップ**: テストが失敗してもコンテナが終了するように、常にdeferでクリーンアップ
