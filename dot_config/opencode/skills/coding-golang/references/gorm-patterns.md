# GORM と GORM-Gen の使用パターン

このリファレンスは、GORMとGORM-Genを使用したデータベース操作の一般的なパターンを提供します。

## プロジェクトでの使い分け

- **GORM-Genが存在する場合**: 生成されたコードを優先的に使用
- **GORM-Genが存在しない場合**: 素のGORMを使用

## GORM-Gen の使用パターン

### 生成されたコードの基本使用

```go
package main

import (
	"your-project/query" // 生成されたクエリパッケージ
	"gorm.io/gorm"
)

func main() {
	db, err := gorm.Open(...)
	if err != nil {
		panic(err)
	}

	// 生成されたクエリの初期化
	query.SetDefault(db)
}

// ユーザーの取得
func GetUser(userID int64) (*model.User, error) {
	u := query.User

	user, err := u.Where(u.ID.Eq(userID)).First()
	if err != nil {
		return nil, err
	}

	return user, nil
}

// ユーザーの一覧取得
func ListUsers(limit, offset int) ([]*model.User, error) {
	u := query.User

	users, err := u.Limit(limit).Offset(offset).Find()
	if err != nil {
		return nil, err
	}

	return users, nil
}
```

### CRUD操作（GORM-Gen）

```go
// Create
func CreateUser(name, email string) (*model.User, error) {
	u := query.User

	user := &model.User{
		Name:  name,
		Email: email,
	}

	if err := u.Create(user); err != nil {
		return nil, err
	}

	return user, nil
}

// Read
func GetUserByEmail(email string) (*model.User, error) {
	u := query.User

	user, err := u.Where(u.Email.Eq(email)).First()
	if err != nil {
		return nil, err
	}

	return user, nil
}

// Update
func UpdateUser(userID int64, name string) error {
	u := query.User

	_, err := u.Where(u.ID.Eq(userID)).Update(u.Name, name)
	return err
}

// 複数フィールドの更新
func UpdateUserFields(userID int64, updates map[string]interface{}) error {
	u := query.User

	_, err := u.Where(u.ID.Eq(userID)).Updates(updates)
	return err
}

// Delete
func DeleteUser(userID int64) error {
	u := query.User

	_, err := u.Where(u.ID.Eq(userID)).Delete()
	return err
}
```

### 条件付きクエリ（GORM-Gen）

```go
func SearchUsers(keyword string, status string, page, pageSize int) ([]*model.User, int64, error) {
	u := query.User

	q := u.Where()

	// 動的条件追加
	if keyword != "" {
		q = q.Where(u.Name.Like("%" + keyword + "%"))
	}

	if status != "" {
		q = q.Where(u.Status.Eq(status))
	}

	// 総数取得
	count, err := q.Count()
	if err != nil {
		return nil, 0, err
	}

	// ページネーション
	offset := (page - 1) * pageSize
	users, err := q.Limit(pageSize).Offset(offset).Find()
	if err != nil {
		return nil, 0, err
	}

	return users, count, nil
}
```

### リレーション（GORM-Gen）

```go
// Preloadを使用した関連データの取得
func GetUserWithPosts(userID int64) (*model.User, error) {
	u := query.User

	user, err := u.Preload(u.Posts).Where(u.ID.Eq(userID)).First()
	if err != nil {
		return nil, err
	}

	return user, nil
}

// 複数のリレーションをPreload
func GetUserWithRelations(userID int64) (*model.User, error) {
	u := query.User

	user, err := u.
		Preload(u.Posts).
		Preload(u.Profile).
		Preload(u.Roles).
		Where(u.ID.Eq(userID)).
		First()
	if err != nil {
		return nil, err
	}

	return user, nil
}

// JOIN を使用したクエリ
func GetUsersWithActivePosts() ([]*model.User, error) {
	u := query.User
	p := query.Post

	users, err := u.
		LeftJoin(p, u.ID.EqCol(p.UserID)).
		Where(p.Status.Eq("published")).
		Distinct(u.ID).
		Find()

	return users, err
}
```

### トランザクション（GORM-Gen）

```go
func CreateUserWithProfile(name, email, bio string) error {
	return query.Q.Transaction(func(tx *query.Query) error {
		// ユーザー作成
		user := &model.User{
			Name:  name,
			Email: email,
		}
		if err := tx.User.Create(user); err != nil {
			return err
		}

		// プロフィール作成
		profile := &model.Profile{
			UserID: user.ID,
			Bio:    bio,
		}
		if err := tx.Profile.Create(profile); err != nil {
			return err
		}

		return nil
	})
}
```

## 素のGORMの使用パターン

### モデル定義

```go
package model

import (
	"time"
	"gorm.io/gorm"
)

type User struct {
	ID        int64          `gorm:"primaryKey"`
	Name      string         `gorm:"not null"`
	Email     string         `gorm:"uniqueIndex;not null"`
	Status    string         `gorm:"default:active"`
	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt gorm.DeletedAt `gorm:"index"`

	// リレーション
	Posts   []Post   `gorm:"foreignKey:UserID"`
	Profile *Profile `gorm:"foreignKey:UserID"`
}

type Post struct {
	ID        int64  `gorm:"primaryKey"`
	UserID    int64  `gorm:"not null;index"`
	Title     string `gorm:"not null"`
	Content   string `gorm:"type:text"`
	Status    string `gorm:"default:draft"`
	CreatedAt time.Time
	UpdatedAt time.Time

	User User `gorm:"foreignKey:UserID"`
}

type Profile struct {
	ID     int64  `gorm:"primaryKey"`
	UserID int64  `gorm:"uniqueIndex;not null"`
	Bio    string `gorm:"type:text"`
	Avatar string

	User User `gorm:"foreignKey:UserID"`
}
```

### CRUD操作（素のGORM）

```go
// Create
func CreateUser(db *gorm.DB, name, email string) (*User, error) {
	user := &User{
		Name:  name,
		Email: email,
	}

	if err := db.Create(user).Error; err != nil {
		return nil, err
	}

	return user, nil
}

// Read
func GetUser(db *gorm.DB, userID int64) (*User, error) {
	var user User
	if err := db.First(&user, userID).Error; err != nil {
		return nil, err
	}

	return &user, nil
}

func GetUserByEmail(db *gorm.DB, email string) (*User, error) {
	var user User
	if err := db.Where("email = ?", email).First(&user).Error; err != nil {
		return nil, err
	}

	return &user, nil
}

// Update
func UpdateUser(db *gorm.DB, userID int64, name string) error {
	return db.Model(&User{}).Where("id = ?", userID).Update("name", name).Error
}

// 複数フィールドの更新
func UpdateUserFields(db *gorm.DB, userID int64, updates map[string]interface{}) error {
	return db.Model(&User{}).Where("id = ?", userID).Updates(updates).Error
}

// Delete（論理削除）
func DeleteUser(db *gorm.DB, userID int64) error {
	return db.Delete(&User{}, userID).Error
}

// 物理削除
func HardDeleteUser(db *gorm.DB, userID int64) error {
	return db.Unscoped().Delete(&User{}, userID).Error
}
```

### クエリ（素のGORM）

```go
// リスト取得
func ListUsers(db *gorm.DB, limit, offset int) ([]User, error) {
	var users []User
	if err := db.Limit(limit).Offset(offset).Find(&users).Error; err != nil {
		return nil, err
	}

	return users, nil
}

// 条件付き検索
func SearchUsers(db *gorm.DB, keyword string, status string) ([]User, error) {
	var users []User
	query := db.Model(&User{})

	if keyword != "" {
		query = query.Where("name LIKE ?", "%"+keyword+"%")
	}

	if status != "" {
		query = query.Where("status = ?", status)
	}

	if err := query.Find(&users).Error; err != nil {
		return nil, err
	}

	return users, nil
}

// カウント取得
func CountUsers(db *gorm.DB, status string) (int64, error) {
	var count int64
	query := db.Model(&User{})

	if status != "" {
		query = query.Where("status = ?", status)
	}

	if err := query.Count(&count).Error; err != nil {
		return 0, err
	}

	return count, nil
}

// 存在チェック
func UserExists(db *gorm.DB, email string) (bool, error) {
	var count int64
	err := db.Model(&User{}).Where("email = ?", email).Count(&count).Error
	return count > 0, err
}
```

### リレーション（素のGORM）

```go
// Preloadを使用
func GetUserWithPosts(db *gorm.DB, userID int64) (*User, error) {
	var user User
	if err := db.Preload("Posts").First(&user, userID).Error; err != nil {
		return nil, err
	}

	return &user, nil
}

// 複数のPreload
func GetUserWithRelations(db *gorm.DB, userID int64) (*User, error) {
	var user User
	if err := db.
		Preload("Posts").
		Preload("Profile").
		First(&user, userID).Error; err != nil {
		return nil, err
	}

	return &user, nil
}

// 条件付きPreload
func GetUserWithPublishedPosts(db *gorm.DB, userID int64) (*User, error) {
	var user User
	if err := db.
		Preload("Posts", "status = ?", "published").
		First(&user, userID).Error; err != nil {
		return nil, err
	}

	return &user, nil
}

// JOIN
func GetUsersWithActivePosts(db *gorm.DB) ([]User, error) {
	var users []User
	if err := db.
		Joins("LEFT JOIN posts ON posts.user_id = users.id").
		Where("posts.status = ?", "published").
		Distinct("users.id").
		Find(&users).Error; err != nil {
		return nil, err
	}

	return users, nil
}
```

### トランザクション（素のGORM）

```go
func CreateUserWithProfile(db *gorm.DB, name, email, bio string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		// ユーザー作成
		user := &User{
			Name:  name,
			Email: email,
		}
		if err := tx.Create(user).Error; err != nil {
			return err
		}

		// プロフィール作成
		profile := &Profile{
			UserID: user.ID,
			Bio:    bio,
		}
		if err := tx.Create(profile).Error; err != nil {
			return err
		}

		return nil
	})
}

// 手動トランザクション
func TransferBalance(db *gorm.DB, fromUserID, toUserID int64, amount float64) error {
	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if err := tx.Error; err != nil {
		return err
	}

	// 送信者の残高を減らす
	if err := tx.Model(&Account{}).
		Where("user_id = ?", fromUserID).
		UpdateColumn("balance", gorm.Expr("balance - ?", amount)).
		Error; err != nil {
		tx.Rollback()
		return err
	}

	// 受信者の残高を増やす
	if err := tx.Model(&Account{}).
		Where("user_id = ?", toUserID).
		UpdateColumn("balance", gorm.Expr("balance + ?", amount)).
		Error; err != nil {
		tx.Rollback()
		return err
	}

	return tx.Commit().Error
}
```

### バルク操作

```go
// バルクインサート
func BulkCreateUsers(db *gorm.DB, users []User) error {
	return db.Create(&users).Error
}

// バッチ処理
func ProcessUsersInBatches(db *gorm.DB, batchSize int, fn func([]User) error) error {
	return db.FindInBatches(&[]User{}, batchSize, func(tx *gorm.DB, batch int) error {
		var users []User
		if err := tx.Find(&users).Error; err != nil {
			return err
		}

		return fn(users)
	}).Error
}

// バルクアップデート
func BulkUpdateUserStatus(db *gorm.DB, userIDs []int64, status string) error {
	return db.Model(&User{}).
		Where("id IN ?", userIDs).
		Update("status", status).
		Error
}
```

### Raw SQL とスキャン

```go
// Raw SQLクエリ
func GetUserStats(db *gorm.DB) ([]UserStat, error) {
	var stats []UserStat
	err := db.Raw(`
		SELECT
			users.id,
			users.name,
			COUNT(posts.id) as post_count
		FROM users
		LEFT JOIN posts ON posts.user_id = users.id
		GROUP BY users.id, users.name
	`).Scan(&stats).Error

	return stats, err
}

type UserStat struct {
	ID        int64
	Name      string
	PostCount int
}

// Exec（INSERT/UPDATE/DELETE）
func ExecuteCustomQuery(db *gorm.DB) error {
	return db.Exec(`
		UPDATE users
		SET status = 'inactive'
		WHERE last_login_at < NOW() - INTERVAL 30 DAY
	`).Error
}
```

## エラーハンドリング

```go
import (
	"errors"
	"gorm.io/gorm"
)

func GetUser(db *gorm.DB, userID int64) (*User, error) {
	var user User
	err := db.First(&user, userID).Error

	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, fmt.Errorf("user not found: %d", userID)
		}
		return nil, fmt.Errorf("database error: %w", err)
	}

	return &user, nil
}

func CreateUser(db *gorm.DB, user *User) error {
	err := db.Create(user).Error
	if err != nil {
		// 重複キーエラーのチェック（PostgreSQL）
		if strings.Contains(err.Error(), "duplicate key") {
			return fmt.Errorf("user already exists")
		}
		return fmt.Errorf("failed to create user: %w", err)
	}

	return nil
}
```

## ベストプラクティス

1. **GORM-Gen優先**: プロジェクトにGORM-Genが存在する場合は生成されたコードを使用
2. **トランザクション**: 複数の関連操作は必ずトランザクション内で実行
3. **Preload**: N+1問題を避けるため、関連データはPreloadを使用
4. **エラーハンドリング**: `gorm.ErrRecordNotFound`などの特定エラーを適切に処理
5. **インデックス**: 頻繁に検索するカラムにはインデックスを設定
6. **ソフトデリート**: 論理削除が必要な場合は`gorm.DeletedAt`を使用
7. **バッチ処理**: 大量データ処理はバッチで実行してメモリ効率を向上
8. **Raw SQL**: 複雑なクエリはRaw SQLを使用して可読性とパフォーマンスを確保
