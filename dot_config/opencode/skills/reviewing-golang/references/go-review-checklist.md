# Go特有のレビュー観点チェックリスト

## 1. ゴルーチンとチャネルの安全性

### ゴルーチンリーク

**確認ポイント:**

- [ ] すべてのゴルーチンに終了条件があるか
- [ ] コンテキストのキャンセルに対応しているか
- [ ] 停止シグナル（done channel等）が適切に使われているか

**危険パターン:**

```go
// NG: 終了条件がない
go func() {
    for {
        // 無限ループ
    }
}()

// OK: キャンセル対応
go func() {
    for {
        select {
        case <-ctx.Done():
            return
        case item := <-ch:
            process(item)
        }
    }
}()
```

### 無制限のゴルーチン生成

**確認ポイント:**

- [ ] ループ内でのgoroutine生成に制限があるか
- [ ] ワーカープールパターンを検討すべきか

**危険パターン:**

```go
// NG: リクエストごとに無制限にgoroutine生成
for _, item := range items {
    go process(item) // 1000万件あったら？
}

// OK: ワーカープールで制限
sem := make(chan struct{}, maxWorkers)
for _, item := range items {
    sem <- struct{}{}
    go func(item Item) {
        defer func() { <-sem }()
        process(item)
    }(item)
}
```

### データ競合

**確認ポイント:**

- [ ] 共有変数へのアクセスが同期されているか
- [ ] `go run -race` でテストされているか

---

## 2. チャネル操作

### デッドロック

**確認ポイント:**

- [ ] 送信と受信のバランスが取れているか
- [ ] unbuffered channelの送信がブロックしないか
- [ ] チャネルのクローズタイミングが適切か

**危険パターン:**

```go
// NG: 受信者がいないのに送信
ch := make(chan error)
go func() {
    if err != nil {
        ch <- err // 永久にブロック
    }
}()
return nil // 関数が先に終了

// OK: buffered channelまたは確実な受信
ch := make(chan error, 1)
```

### チャネルのクローズ

**確認ポイント:**

- [ ] チャネルは送信側でクローズされているか
- [ ] 二重クローズの防止がされているか
- [ ] nilチャネルへの操作がないか

---

## 3. リソース管理

### Close()の呼び出し

**確認ポイント:**

- [ ] `sql.Rows` がClose()されているか
- [ ] `sql.Conn` がClose()されているか
- [ ] `http.Response.Body` がClose()されているか
- [ ] `os.File` がClose()されているか
- [ ] `io.ReadCloser` がClose()されているか

**推奨パターン:**

```go
rows, err := db.Query(...)
if err != nil {
    return err
}
defer rows.Close() // 必ずエラーチェックの後

resp, err := http.Get(url)
if err != nil {
    return err
}
defer resp.Body.Close() // 必ずエラーチェックの後
```

### defer の使用

**確認ポイント:**

- [ ] deferがエラーチェックの後に配置されているか
- [ ] deferの実行順序（LIFO）が意図通りか
- [ ] deferでのエラー処理が適切か

**危険パターン:**

```go
// NG: エラーチェック前のdefer
f, err := os.Open(name)
defer f.Close() // fがnilの場合panic
if err != nil {
    return err
}

// OK: エラーチェック後
f, err := os.Open(name)
if err != nil {
    return err
}
defer f.Close()
```

---

## 4. エラーハンドリング

### 無視されたエラー

**確認ポイント:**

- [ ] すべての戻り値のエラーがチェックされているか
- [ ] `rows.Scan()` のエラーがチェックされているか
- [ ] `rows.Err()` がイテレーション後にチェックされているか

**必須パターン:**

```go
for rows.Next() {
    if err := rows.Scan(&v); err != nil {
        return err
    }
}
if err := rows.Err(); err != nil {
    return err // イテレーション中のエラーを確認
}
```

### エラーラッピング

**確認ポイント:**

- [ ] エラーに適切なコンテキストが付与されているか
- [ ] `%w` を使ってエラーをラップしているか

```go
// NG: コンテキストなし
return err

// OK: コンテキスト付与
return fmt.Errorf("failed to load config %s: %w", name, err)
```

---

## 5. コンテキスト

### コンテキスト伝播

**確認ポイント:**

- [ ] 関数がcontext.Context を第一引数で受け取っているか
- [ ] `context.Background()` の使用が適切か（ルートのみ）
- [ ] 長時間処理でキャンセルに対応しているか

**危険パターン:**

```go
// NG: contextを無視
func Process(ctx context.Context) error {
    db.Query("SELECT ...") // ctxを使っていない
}

// OK: contextを伝播
func Process(ctx context.Context) error {
    db.QueryContext(ctx, "SELECT ...")
}
```

### タイムアウト

**確認ポイント:**

- [ ] HTTP Clientにタイムアウトが設定されているか
- [ ] データベース操作にタイムアウトがあるか

```go
// NG: タイムアウトなし
client := &http.Client{}

// OK: タイムアウト設定
client := &http.Client{
    Timeout: 30 * time.Second,
}
```

---

## 6. 同期プリミティブ

### Mutex

**確認ポイント:**

- [ ] すべてのコードパスでUnlockが保証されているか
- [ ] deferを使ったUnlockが推奨

**危険パターン:**

```go
// NG: エラーパスでunlock漏れ
mu.Lock()
if err := doSomething(); err != nil {
    return err // unlock漏れ
}
mu.Unlock()

// OK: deferで保証
mu.Lock()
defer mu.Unlock()
```

### sync.WaitGroup

**確認ポイント:**

- [ ] Add()がgoroutine起動前に呼ばれているか
- [ ] Done()がgoroutine内で確実に呼ばれているか

```go
// NG: Add()がgoroutine内
for i := 0; i < n; i++ {
    go func() {
        wg.Add(1) // 競合状態
        defer wg.Done()
    }()
}

// OK: Add()はgoroutine外
for i := 0; i < n; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
    }()
}
```

### sync.Once

**確認ポイント:**

- [ ] 一度だけ実行すべき初期化に使われているか
- [ ] チャネルのクローズなどに使用を検討

---

## 7. テストコード固有

### テーブル駆動テスト

- [ ] テストケースが構造化されているか
- [ ] 正常系・異常系・エッジケースが網羅されているか
- [ ] テストケース名が説明的か

### assert/require の使い分け

- [ ] 前提条件には `require` を使用しているか
- [ ] 検証には `assert` を使用しているか

### モック

- [ ] mockeryで生成されたモックを使用しているか
- [ ] `mock.Anything` の使用は必要最小限か
- [ ] モックの期待値が適切に設定されているか

### 並列テスト

- [ ] `t.Parallel()` 使用時に競合状態がないか
- [ ] 共有リソースへのアクセスが同期されているか
