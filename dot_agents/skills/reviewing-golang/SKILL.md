---
name: reviewing-golang
description: Goコードレビューや修正後検証で使用。並行処理、goroutineリーク、エラー処理、リソース管理を確認する。
invocation: auto
ecc-imports:
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: agents/go-reviewer.md
    sections-merged: []
    conflicts:
      - "Review Priorities"
      - "Diagnostic Commands"
      - "Approval Criteria"
    imported-at: 2026-04-27T00:00:00+09:00
---

# Go Code Reviewer (reviewing-golang)

## Overview

Go特有の観点でコードレビューを行うスキル。プロダクトコード・テストコード両方に対応し、coding-golangとtesting-golangスキルの規約に準拠しているかも確認する。

## 関連スキルへの参照

| スキル             | 確認内容                                                     |
| ------------------ | ------------------------------------------------------------ |
| **coding-golang**  | プロダクトコードの規約（chi、GORM、エラーハンドリング等）    |
| **testing-golang** | テストコードの規約（testify、mockery、テーブル駆動テスト等） |

**REQUIRED:** レビュー対象がプロダクトコードなら coding-golang、テストコードなら testing-golang の規約に準拠しているか確認すること。

## レビュー観点

### 1. Go特有の問題（最重要）

**REQUIRED**: レビュー開始時に `references/go-review-checklist.md` を **Read ツールで読み込む**こと。リンクを見るだけでなく、ファイルの全内容を読み込んでからレビューを行う。特に修正が状態遷移・ライフサイクル管理・クリーンアップ処理に関わる場合、「並行ライフサイクルの安全性」セクションのチェックリストを全項目適用すること。

| カテゴリ               | 確認項目                                       |
| ---------------------- | ---------------------------------------------- |
| **ゴルーチン安全性**   | リーク、無制限生成、競合状態                   |
| **チャネル**           | デッドロック、クローズ忘れ、nil送受信          |
| **リソース管理**       | Close()呼び出し、defer使用、コネクションプール |
| **エラーハンドリング** | 無視されたエラー、rows.Err()、ラッピング       |
| **コンテキスト**       | 伝播、キャンセル対応、タイムアウト             |
| **同期**               | Mutex unlock漏れ、WaitGroup誤用、sync.Once     |

### 2. よくある問題パターン

詳細は [common-go-issues.md](references/common-go-issues.md) を参照。

- ループ変数のキャプチャ
- nilインターフェース vs nil値
- time.Afterのリーク
- 空スライス vs nilスライス

### 3. コード品質

- 命名規則（Go慣習に従っているか）
- 関数の単一責任
- 早期リターン
- マジックナンバーの回避

### 4. テストコード（該当する場合）

- テーブル駆動テストの使用
- assert/requireの適切な使い分け
- エッジケースのカバー
- モックの適切な使用

### 5. セキュリティ

- SQLインジェクション
- 入力バリデーション
- 機密情報の扱い
- **gosec** で静的セキュリティ解析を実行する: `gosec ./...`
- 外部呼び出し（HTTP/DB/gRPC等）には必ず `context.WithTimeout` でタイムアウトを設定する
  ```go
  ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
  defer cancel()
  ```
- secrets は `os.Getenv("KEY")` の戻り値を空文字チェックし、未設定なら error を返す（silent failure 防止）
  ```go
  apiKey := os.Getenv("API_KEY")
  if apiKey == "" {
      return fmt.Errorf("API_KEY not configured")
  }
  ```

## 必須チェックリスト

レビュー時に以下を必ず確認すること：

### Critical（必ず確認）

- [ ] sql.Rows, sql.Conn, http.Response.Body などがClose()されているか
- [ ] ゴルーチンが適切に終了するか（リーク防止）
- [ ] Mutexのunlockがすべてのパスで保証されているか
- [ ] エラーが無視されていないか
- [ ] コンテキストが適切に伝播されているか
- [ ] 複数のRepository書き込み操作がトランザクションで囲まれているか
- [ ] 読み取り→判断→書き込み（TOCTOU）パターンが同一トランザクション内にあるか

### Critical（並行ライフサイクル — 状態遷移・クリーンアップ・リソースライフサイクルを含む修正の場合）

修正が状態遷移、クリーンアップ処理、リソースのライフサイクル管理に関わる場合、詳細チェックリストは [go-review-checklist.md](references/go-review-checklist.md) §並行ライフサイクルの安全性 を参照し、全項目のOK/NG判定を出力に含めること。

### High（重要）

- [ ] チャネル操作でデッドロックの可能性がないか
- [ ] 並行処理でデータ競合がないか
- [ ] for loop内でのtime.After使用がないか
- [ ] nilインターフェースのチェックが正しいか

### Medium

- [ ] HTTP Clientにタイムアウトが設定されているか
- [ ] deferの実行順序が意図通りか
- [ ] エラーに適切なコンテキストが付与されているか

## 出力フォーマット

レビュー結果は以下の形式で整理すること：

```markdown
## レビュー結果

### Critical Issues

- [行番号] 問題の説明と修正案

### High Priority

- [行番号] 問題の説明と修正案

### Medium Priority

- [行番号] 問題の説明と修正案

### Suggestions

- 改善提案

### 確認事項

- coding-golang/testing-golang 規約への準拠: [OK/要修正]
- プロジェクト固有の規約: [OK/要修正/未確認]
```

## リファレンス一覧

| ファイル                                                    | 内容                         |
| ----------------------------------------------------------- | ---------------------------- |
| [go-review-checklist.md](references/go-review-checklist.md) | Go特有のレビュー観点詳細     |
| [common-go-issues.md](references/common-go-issues.md)       | よくある問題パターンと修正例 |

## ECC 由来: agents/go-reviewer.md

> ECC base commit `4e66b2882da9afb9747468b08a253ca2f09c85f3` の `agents/go-reviewer.md`（76 行）を検証したが、本 skill の構造（`references/` に詳細を委譲する索引型 + プロジェクト固有規約優先）と異なるため統合せず、**全 H2 を conflicts として記録**。
>
> ECC `go-reviewer` は CRITICAL/HIGH/MEDIUM の severity 階層を持つレビューチェックリスト形式:
>
> - **Review Priorities** (severity 階層): SQL injection / Command injection / Race conditions / Goroutine leaks / errors.Is/As / Mutex misuse 等
>   - 既存の §レビュー観点 / §必須チェックリスト + `references/go-review-checklist.md` / `references/common-go-issues.md` で同等の網羅性をカバー（重複につき conflicts）
> - **Diagnostic Commands**: `go vet` / `staticcheck` / `golangci-lint` / `go test -race` / `govulncheck`
>   - 必要に応じて `references/diagnostic-commands.md` として将来配置可能（本 spec のスコープ外）
> - **Approval Criteria**: Approve/Warning/Block の判定基準
>   - 本 skill の §レビュー結果 で同等

## /ECC 由来: agents/go-reviewer.md
