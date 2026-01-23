---
name: conventional-commit
description: Conventional Commits形式のコミットメッセージ作成や種類選定を求められた時に使う。
---

# Conventional Commitsガイド

## 目的

- 変更内容を一貫した形式で伝える。
- 自動的なCHANGELOG生成やリリースノート作成を支援する。

## 形式

```
<type>(<scope>): <subject>
```

- `<scope>` は任意。対象が明確なら指定し、迷う場合は省略する。
- 破壊的変更は `<type>!` またはフッターで明示する。

### 破壊的変更

```
feat!: drop legacy auth flow

BREAKING CHANGE: legacy auth endpoints are removed
```

## type一覧 (標準)

- feat: 新機能
- fix: バグ修正
- docs: ドキュメントのみ
- style: フォーマットや空白などの修正 (動作変更なし)
- refactor: リファクタリング
- perf: 性能改善
- test: テスト追加/修正
- build: ビルドや依存関係
- ci: CI設定
- chore: 雑務やメタ作業
- revert: 差し戻し

## 英語コミットメッセージのルール

- `<subject>` は命令形で書く。
- 先頭は小文字にする。
- 末尾にピリオドを付けない。

## 例

```
feat(api): add batch export endpoint
fix(ui): handle empty state rendering
docs: update install instructions
refactor(auth): split token validation
perf(db): reduce query round trips
test: cover edge cases in parser
build: bump pnpm to 9.0
ci: add lint job
chore: clean up temp scripts
revert: revert "feat: add oauth login"
```

## チェックリスト

- typeは変更内容に合っている。
- scopeは必要な時だけ付けている。
- subjectは英語の命令形で簡潔。
- 破壊的変更は `!` か `BREAKING CHANGE:` で明示している。
