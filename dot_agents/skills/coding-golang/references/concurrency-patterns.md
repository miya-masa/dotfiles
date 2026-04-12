# 並行処理の実装パターン

このリファレンスは、並行処理を含むGoコードの実装パターンを提供する。
タスクが並行処理を含む場合（goroutine間の協調、状態の遷移、リソースのライフサイクル管理等）に参照すること。

## 1. 遷移期間の設計

旧状態と新状態が共存する期間（遷移期間）がある場合、**すべての操作の挙動を明示的に定義する**。

### 原則

- 遷移期間中に発生しうるすべての操作を列挙する
- 各操作が旧状態・新状態のどちらに作用するか明確にする
- 遷移が完了したかどうかを判定する条件を定義する

### パターン: Check-then-Act の原子性

```go
// NG: チェックと操作が分離 — 間にstateが変わる可能性
if !isDisconnected() {
    disconnect()  // この間に新しい接続が来ると競合
}

// OK: ロック内でチェックと操作を原子的に実行
mu.Lock()
defer mu.Unlock()
if !isDisconnected() {
    disconnect()
}
```

### 具体例: 旧リソースがまだ生存中に新リソースが確立される場合

タイムアウトやヘルスチェック等の非同期検出に依存する切断検出では、
旧リソースがまだ「接続中」と認識されている間に新リソースの確立要求が来る場合がある。
正当な所有権が証明できるなら（トークン、セッションID等）、旧リソースをforce-closeして
新リソースの確立を進める。非同期検出の完了を待たない。

## 2. クリーンアップの非破壊原則

クリーンアップ処理（Close, Shutdown, Cleanup等）は「リソースの解放」だが、並行して新しい状態が確立されている可能性を常に考慮する。

### 原則

- クリーンアップの前に現在の状態を読み取る
- 既に遷移済み（新しい状態が確立済み）なら書き込みをスキップ
- クリーンアップはべき等に設計する（複数回呼ばれても安全）

### パターン: Read-before-Write in Cleanup

```go
func (h *Handler) Close() error {
    // リポジトリから最新の状態を読み取る
    current, err := h.repo.Load(h.streamID)
    if err != nil {
        return fmt.Errorf("failed to load current state: %w", err)
    }

    // 既に新しいセッションで更新済みならスキップ
    if current.DisconnectedAt != nil {
        return nil // 既にクローズ済み
    }
    if current.ResumeToken != h.cachedResumeToken {
        return nil // トークンがローテート済み（新Resumeが完了）
    }

    // 安全に書き込み
    current.DisconnectedAt = timePtr(time.Now())
    return h.repo.Save(current)
}
```

## 3. 実装非依存の設計

interfaceを介して状態を管理する場合、特定の実装（インメモリ、DB、外部サービス等）の挙動に依存しない設計にする。「現在の実装を別の実装に差し替えても同じ結果になるか」を設計基準にする。

### 原則

- 特定の実装固有の挙動に依存しない（インメモリ参照共有、キャッシュの暗黙的同期、接続プールの共有など）
- interfaceの呼び出し元が、実装の内部状態（ポインタ、参照）に依存しない
- テストでは状態のラウンドトリップ（Save→Load）を検証し、実装を差し替えても動作することを確認する

### 検証手順

該当するinterfaceの**具体実装のSave/Find/Load等のメソッドをRead**し、以下を確認する:
- コレクションフィールド（map, slice）がディープコピーされているか
- Save後に元オブジェクトを変更しても、保存済みデータに影響しないか
- Findで取得した値を変更しても、ストレージ内のデータに影響しないか

### 危険パターン

```go
// NG: 呼び出し元がmap参照を共有し、暗黙的に状態が同期される
state := &StreamState{DataIDAliases: make(map[uint32]DataID)}
repo.Save(state)
// ... state.DataIDAliases に後から追加 ...
// InmemRepoでは共有参照で「動く」が、DB-backedでは失われる

// OK: 状態が変化したらinterface経由で明示的に保存
state.DataIDAliases[newAlias] = newDataID
repo.Save(state) // 明示的に永続化
```

## 4. 動的状態の明示的永続化

初期化後に動的に変化する状態は、変化時点でinterface経由で保存する。

### 原則

- 「初期化時に保存したから大丈夫」は不十分 — 動的変化を追跡する
- 状態変化のタイミングでSave()を呼ぶか、バッチ保存の仕組みを用意する
- テストで「初期化→動的変化→Resume/Reload→動的変化が保持されているか」を検証する

### パターン: バッチ保存

```go
// 頻繁な変化はバッチで保存（例: ACK間隔に合わせる）
func (h *Handler) writeAckLoop() {
    for ack := range h.ackCh {
        resp := h.buildAckResponse(ack)
        if resp.HasNewDataIDAliases() {
            if err := h.repo.Save(h.stream); err != nil {
                h.logger.Error("failed to persist stream state", "error", err)
            }
        }
        h.sendAck(resp)
    }
}
```
