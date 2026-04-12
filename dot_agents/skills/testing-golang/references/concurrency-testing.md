# 並行処理のテストパターン

このリファレンスは、並行処理を含むGoコードのテストパターンを提供する。
タスクが並行処理を含む場合に参照すること。

## 1. 並行ライフサイクルテスト

旧/新の状態が同時に動くシナリオのテスト方法。

**REQUIRED**: 並行ライフサイクルに関わるバグ修正では、以下の2つを必ず含めること:
1. チャネルを使ったタイミング制御テスト（操作の順序を明示的に制御して競合を再現）
2. `-race -count=10` での実行（非決定的なバグの検出）

**テスト手法の使い分け:**
- **モックベーステスト**: 「操作Aが呼ばれたか」「引数は正しいか」の検証に適する。状態の最終結果を検証するが、タイミング競合の再現はできない
- **チャネル制御テスト**: 「操作Aの途中に操作Bが割り込む」シナリオの再現に必須。クリーンアップ（Close/Shutdown）と状態更新（Resume/Save）のタイミング競合は、モックでは再現できないためチャネル制御が必要

モックテストとチャネル制御テストは排他ではなく、両方作成すること。

### パターン: チャネルを使ったタイミング制御

```go
func TestResume_WhileOldConnectionClosing(t *testing.T) {
    handler := newTestHandler(t)
    handler.Open(ctx, streamID)

    closeStarted := make(chan struct{})
    closeCanProceed := make(chan struct{})

    mockRepo.OnSave(func(state *StreamState) error {
        close(closeStarted)
        <-closeCanProceed
        return nil
    })

    go func() {
        handler.Close()
    }()

    <-closeStarted

    newHandler := newTestHandler(t)
    err := newHandler.HandleResumeRequest(ctx, validToken)
    require.NoError(t, err)

    close(closeCanProceed)

    state, _ := mockRepo.Load(streamID)
    assert.Equal(t, newHandler.ResumeToken, state.ResumeToken)
}
```

### ポイント

- チャネルで goroutine 間のタイミングを明示的に制御する
- `closeStarted` / `closeCanProceed` パターンで「Close()の途中」を再現
- テスト終了時にすべての goroutine が終了することを `goleak.VerifyNone(t)` で確認

## 2. Repository抽象化テスト

インメモリ以外の実装でも動くことを検証するパターン。

**REQUIRED**: 修正が以下のいずれかに該当する場合、このセクションのテストを必ず作成すること:
- interface経由で状態を保存・復元するコードを変更した（Repository.Save/Find等）
- 特定のinterface実装の挙動（参照共有、キャッシュ等）に依存しない設計に修正した
- 動的に変化する状態の永続化を追加した

作成すべきテスト:
1. **ラウンドトリップテスト**: Save→Load で動的状態が保持されること
2. **参照独立性テスト**: Load した値を変更しても、ストレージ内のデータに影響しないこと

### パターン: シリアライズラウンドトリップテスト

```go
func TestDynamicState_SurvivesRoundTrip(t *testing.T) {
    repo := newTestRepository(t)

    state := &StreamState{
        StreamID:      "stream-1",
        DataIDAliases: map[uint32]DataID{},
    }
    require.NoError(t, repo.Save(state))

    state.DataIDAliases[1] = DataID{Name: "sensor/temperature"}
    require.NoError(t, repo.Save(state))

    loaded, err := repo.Load("stream-1")
    require.NoError(t, err)

    assert.Equal(t, state.DataIDAliases, loaded.DataIDAliases)

    state.DataIDAliases[2] = DataID{Name: "sensor/humidity"}
    assert.NotEqual(t, len(state.DataIDAliases), len(loaded.DataIDAliases),
        "loaded state should be independent of original reference")
}
```

### ポイント

- Save→Loadのラウンドトリップで動的状態が保持されるか検証
- 参照独立性: Loadした値を変更しても元のリポジトリ内データに影響しないか確認
- InmemRepositoryの「偶然の成功」を排除するテスト設計

## 3. レースコンディションテスト

`-race` フラグに加え、意図的にタイミングをずらして競合を再現する手法。

### パターン: 並行操作の確実な発火

```go
func TestConcurrent_CloseAndResume(t *testing.T) {
    handler := newTestHandler(t)
    handler.Open(ctx, streamID)

    var wg sync.WaitGroup
    errs := make(chan error, 2)

    wg.Add(2)
    go func() {
        defer wg.Done()
        errs <- handler.Close()
    }()
    go func() {
        defer wg.Done()
        errs <- handler.HandleResumeRequest(ctx, validToken)
    }()

    wg.Wait()
    close(errs)

    state, _ := repo.Load(streamID)
    assert.True(t,
        state.ResumeToken != "" || state.DisconnectedAt != nil,
        "state must be consistent after concurrent close+resume")
}
```

### 実行方法（REQUIRED）

並行処理のテストは必ず以下のコマンドで実行すること:

```bash
go test -race -count=10 -run TestConcurrent ./...
```

`-race` はデータ競合を検出し、`-count=10` はタイミング依存のバグを複数回実行で捕捉する。テスト設計時にこのコマンドでの実行を前提とすること。

## 4. Close() + 並行操作テスト

Close()と他の操作が同時に走るシナリオの網羅。

### テストケースの列挙方法

```go
func TestClose_ConcurrentWith(t *testing.T) {
    tests := []struct {
        name        string
        concurrent  func(h *Handler) error
    }{
        {
            name: "Resume",
            concurrent: func(h *Handler) error {
                return h.HandleResumeRequest(ctx, validToken)
            },
        },
        {
            name: "DataWrite",
            concurrent: func(h *Handler) error {
                return h.WriteData(ctx, testData)
            },
        },
        {
            name: "AliasRegistration",
            concurrent: func(h *Handler) error {
                return h.RegisterAlias(ctx, newAlias)
            },
        },
    }

    for _, tt := range tests {
        t.Run("Close+"+tt.name, func(t *testing.T) {
            h := newTestHandler(t)
            h.Open(ctx, streamID)

            var wg sync.WaitGroup
            wg.Add(2)
            go func() { defer wg.Done(); h.Close() }()
            go func() { defer wg.Done(); tt.concurrent(h) }()
            wg.Wait()

            assertConsistentState(t, repo, streamID)
        })
    }
}
```

### ポイント

- Close()と並行して実行されうるすべての操作を列挙してテーブル駆動テストにする
- 各組み合わせで最終状態が整合していることを検証
- `-race -count=10` で実行して非決定的なバグを検出
