# よくあるGoの問題パターン

## 1. ループ変数のキャプチャ

### 問題

Go 1.21以前では、ループ変数はイテレーションごとに同じメモリを再利用する。

```go
// NG: Go 1.21以前で問題
for i, item := range items {
    go func() {
        process(i, item) // 最後の値が使われる
    }()
}
```

### 修正

```go
// OK: 引数として渡す
for i, item := range items {
    go func(i int, item Item) {
        process(i, item)
    }(i, item)
}

// OK: Go 1.22以降 (GOEXPERIMENT=loopvar または Go 1.22+ デフォルト)
// ループ変数がイテレーションごとに新しくなる
```

### 注意

Go 1.22以降でも、明示的に引数として渡す方がコードの意図が明確になる。

---

## 2. nilインターフェース vs nil値

### 問題

インターフェースは「型」と「値」の2つの要素を持つ。値がnilでも型があれば、インターフェースはnilではない。

```go
func GetError() error {
    var err *MyError = nil
    return err // errはnil、だがerror interfaceとしてはnilではない
}

func main() {
    err := GetError()
    if err != nil {
        // ここに来る！errはnilではない
        fmt.Println("error:", err)
    }
}
```

### 修正

```go
// OK: 明示的にnilを返す
func GetError() error {
    var err *MyError = nil
    if err == nil {
        return nil // error interface として nil
    }
    return err
}
```

### チェック方法

```go
// reflectを使って確認（デバッグ用）
import "reflect"

func isNilInterface(i interface{}) bool {
    if i == nil {
        return true
    }
    v := reflect.ValueOf(i)
    return v.Kind() == reflect.Ptr && v.IsNil()
}
```

---

## 3. time.After のメモリリーク

### 問題

`time.After()` は内部でチャネルとタイマーを作成し、タイマーが発火するまでGCされない。

```go
// NG: ループ内でtime.Afterを使うとリーク
for {
    select {
    case <-ch:
        // process
    case <-time.After(5 * time.Second):
        // timeout
    }
}
```

### 修正

```go
// OK: time.Timerを再利用
timer := time.NewTimer(5 * time.Second)
defer timer.Stop()

for {
    select {
    case <-ch:
        if !timer.Stop() {
            <-timer.C
        }
        timer.Reset(5 * time.Second)
    case <-timer.C:
        // timeout
        timer.Reset(5 * time.Second)
    }
}
```

---

## 4. 空スライス vs nilスライス

### 問題

`nil` スライスと空スライス `[]T{}` は異なる。JSONエンコードの結果も異なる。

```go
var nilSlice []int      // nil
emptySlice := []int{}   // 空だがnilではない

json.Marshal(nilSlice)   // null
json.Marshal(emptySlice) // []
```

### 推奨

```go
// APIレスポンスでは空スライスを返す方が扱いやすい
func GetItems() []Item {
    items := []Item{} // nilではなく空スライスで初期化
    // ...
    return items
}
```

---

## 5. defer と名前付き戻り値

### 問題

deferはreturnの後、関数が実際にリターンする前に実行される。名前付き戻り値と組み合わせると混乱を招く。

```go
func example() (result int) {
    defer func() {
        result++ // 戻り値が変更される
    }()
    return 0 // 実際には1が返る
}
```

### 注意点

- deferでエラーを処理する場合は名前付き戻り値を活用できる
- ただし意図が明確になるようコメントを付ける

```go
func readFile(path string) (data []byte, err error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr // クローズエラーを戻り値に設定
        }
    }()
    return io.ReadAll(f)
}
```

---

## 6. チャネルの二重クローズ

### 問題

すでにクローズされたチャネルを再度クローズするとpanic。

```go
// NG: 複数のgoroutineからclose可能
close(ch)
close(ch) // panic: close of closed channel
```

### 修正

```go
// OK: sync.Onceで一度だけクローズ
type SafeChannel struct {
    ch   chan int
    once sync.Once
}

func (s *SafeChannel) Close() {
    s.once.Do(func() {
        close(s.ch)
    })
}
```

---

## 7. append のスライス共有

### 問題

appendは容量が足りる場合、元の配列を共有する。

```go
original := make([]int, 3, 6)
original[0], original[1], original[2] = 1, 2, 3

slice1 := append(original, 4) // 容量内
slice2 := append(original, 5) // 同じ配列を上書き

fmt.Println(slice1) // [1 2 3 5] ← 4ではなく5
fmt.Println(slice2) // [1 2 3 5]
```

### 修正

```go
// OK: コピーしてから追加
slice1 := append([]int(nil), original...)
slice1 = append(slice1, 4)
```

---

## 8. mapの並行アクセス

### 問題

mapは並行安全ではない。同時読み書きでpanic。

```go
// NG: 並行アクセスでpanic
m := make(map[string]int)
go func() { m["a"] = 1 }()
go func() { _ = m["a"] }()
```

### 修正

```go
// OK: sync.Mutexで保護
var mu sync.Mutex
m := make(map[string]int)

go func() {
    mu.Lock()
    m["a"] = 1
    mu.Unlock()
}()

// または sync.Map を使用（読み取りが多い場合）
var sm sync.Map
sm.Store("a", 1)
v, _ := sm.Load("a")
```

---

## 9. HTTPレスポンスボディの読み残し

### 問題

レスポンスボディを完全に読まないとコネクションが再利用されない。

```go
// NG: ボディを読まずにクローズ
resp, _ := http.Get(url)
resp.Body.Close() // コネクション再利用不可
```

### 修正

```go
// OK: 完全に読み切る
resp, _ := http.Get(url)
defer resp.Body.Close()
io.Copy(io.Discard, resp.Body) // 残りを破棄
```

---

## 10. context.WithCancel のリーク

### 問題

`context.WithCancel` で作成したcontextは、使い終わったらキャンセルしないとリーク。

```go
// NG: キャンセルしない
ctx, _ := context.WithCancel(parent) // cancel関数を無視
doSomething(ctx)
```

### 修正

```go
// OK: deferでキャンセル
ctx, cancel := context.WithCancel(parent)
defer cancel()
doSomething(ctx)
```
