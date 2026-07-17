---
name: review-respond
description: .review/review_comments.yaml のレビュー指摘に対応する時に使用。「レビュー対応」「review comments」
---

# Review Respond

`.review/review_comments.yaml` に保存されたレビューコメントを読み取り、各指摘に対応する。

## YAML フォーマット

```yaml
reviews:
  - file: path/to/file.go        # 対象ファイル（プロジェクトルート相対）
    start_line: 54                # 開始行（1-indexed）
    end_line: 61                  # 終了行
    start_col: 1                  # 開始列
    end_col: 12                   # 終了列
    severity: medium              # low / medium / high
    timestamp: "2026-04-16T..."   # 記録日時
    comment: |                    # レビューコメント（複数行可）
      指摘内容がここに入る
```

## 対応フロー

1. `.review/review_comments.yaml` を読む
2. severity 順にソートする（high → medium → low）
3. 各コメントについて:
   a. 対象ファイルの該当範囲（前後の文脈を含めて）を読む
   b. コメントの意図を正確に理解する
   c. **不明点や曖昧さがある場合は、必ずユーザーに確認する。推測で対応しない。**
   d. 適切な修正を行う
4. 全コメントの対応後、サマリーを報告する
5. YAML ファイルをアーカイブする

## 不明点の確認（重要）

レビューコメントの意図が曖昧な場合、以下を確認してから対応する:

- コメントが「〜ではないか？」「〜のほうがよいかも」のように曖昧な場合 → 具体的にどうしたいか確認
- 修正方法が複数考えられる場合 → 選択肢を提示して選んでもらう
- コメントがコードの設計意図に関わる場合 → 現在の設計意図を確認

確認なしに推測で対応してはならない。

## ファイル種別に応じたスキル活用

対象ファイルの拡張子に応じて、適切なスキルを使う:

| 拡張子 | スキル |
|--------|--------|
| `.go` | coding-golang（実装）→ reviewing-golang（自己レビュー） |
| その他 | 汎用的に対応 |

## 対応結果の報告

全コメントの対応後、以下の形式で報告する:

```
## レビュー対応結果

### 1. {file}:{start_line}-{end_line} [{severity}]
- **コメント**: {comment の要約}
- **対応**: {何をしたか}
- **ステータス**: 対応済み / 要確認 / 対応不要（理由）
```

## アーカイブ

全コメントの対応が完了したら:

1. `.review/archive/` ディレクトリを作成する（なければ）
2. `review_comments.yaml` を `.review/archive/{timestamp}.yaml` に移動する
   - timestamp 形式: `YYYY-MM-DDTHH-MM-SS`（ファイル名に使えるようコロンをハイフンに置換）
3. 移動完了を報告する
