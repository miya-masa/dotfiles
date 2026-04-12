---
name: feature-workflow
description: >
  機能開発ワークフロー。タスク（仕様書やユーザー指示）から、worktree隔離 +
  機能ブランチ + beads連携 + エージェントチーム(実装者・テスター・レビューアー)で
  並行開発を管理する。「新機能を実装したい」「feature branchで作業したい」等の依頼時に使用。
---

# Feature Workflow

## Overview

タスク入力(仕様ファイル or テキスト指示)から全フェーズを一気に駆動する。

**起動例:**

```
/feature-workflow docs/specs/auth-module.md
/feature-workflow ユーザー認証機能を実装したい
```

## コンテキスト

- Git Status: !`git status`
- Git Branch: !`git branch --show-current`

## Checklist (TaskCreate で管理)

1. Phase 1: 準備 — ブランチ・worktree・beads セットアップ
2. Phase 2: 並行作業 — チーム構成・issue単位で実装→テスト→レビュー
3. Phase 3: 集約 — squash merge・cleanup
4. Phase 4: 完了 — MR作成・epic close

---

## Phase 1: 準備

### 1.1 タスク入力を解析

ARGUMENTS を確認する:

- ファイルパスが渡された場合 → Read ツールで読み込み、仕様を理解する
- テキスト指示の場合 → そのまま要件として扱う
- AskUserQuestion で topic 名（ブランチ名に使う短い英単語）を決定する

### 1.2 デフォルトブランチを特定

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | grep "HEAD branch" | awk '{print $NF}')
# fallback: main or master
```

### 1.3 機能ブランチ作成

```bash
git checkout $DEFAULT_BRANCH
git pull origin $DEFAULT_BRANCH
git checkout -b feature/<topic>
```

### 1.4 worktree 作成

```bash
git worktree add .claude/worktrees/feature-<topic> feature/<topic>
```

worktree のパスに移動して以降の作業を行う。

### 1.5 beads セットアップ

```bash
# beads が未初期化なら
beads init

# epic 作成
beads create --epic "<topic>: <タスク概要>"

# タスクを issue に分解
# 仕様を分析し、独立した実装単位ごとに issue を作成
beads create "<issue title>" --epic <epic-id>
# ... 繰り返し

# 依存関係を設定
beads dep add <issue-id> --blocks <dependent-issue-id>

# 着手可能タスクを確認
beads ready
```

AskUserQuestion で issue の分解結果をユーザーに確認してから Phase 2 に進む。

---

## Phase 2: 並行作業（チーム方式）

### 2.1 着手可能 issue を取得

```bash
beads ready
```

### 2.2 各 issue の作業開始

issue ごとにワーキングブランチと worktree を作成:

```bash
git checkout feature/<topic>
git checkout -b feature/<topic>/<issue-id>
git worktree add .claude/worktrees/feature-<topic>-<issue-id> feature/<topic>/<issue-id>
```

### 2.3 チーム構成

TeamCreate で3人チームを構成する。プロジェクトの主要言語に応じて subagent_type を選択する:

| ロール      | Go プロジェクト  | その他                    | 役割                     |
| ----------- | ---------------- | ------------------------- | ------------------------ |
| implementer | coding-golang    | general-purpose           | 仕様に基づいてコード実装 |
| tester      | testing-golang   | general-purpose           | テスト作成・実行         |
| reviewer    | reviewing-golang | feature-dev:code-reviewer | コード品質・設計レビュー |

**チーム作成:**

```
TeamCreate:
  team_name: "feature-<topic>-<issue-id>"
  description: "<issue title> の実装"
```

**各ロールへの指示:**

implementer への SendMessage:

- worktree パスとブランチ名
- issue の仕様・要件
- 「実装が完了したら報告してください」

tester への SendMessage (implementer 完了後):

- worktree パス
- 「変更箇所のユニットテストと結合テストを作成・実行してください」
- 「テスト失敗時は implementer にフィードバックしてください」

reviewer への SendMessage (tester 通過後):

- worktree パス
- 「コード品質・設計をレビューし、完了条件を検証してください」

### 2.4 フィードバックループ

```
implementer → 実装完了を報告
  ↓
tester → テスト作成・実行
  ↓ テスト失敗
tester → implementer: 失敗内容をフィードバック
implementer → 修正して報告
  ↓ テスト通過
reviewer → レビュー実施
  ↓ 問題あり
reviewer → implementer: 修正指摘
implementer → 修正 → tester → 再テスト
  ↓ 承認
リーダー → beads close <issue-id>
```

### 2.5 ワーキングブランチ完了条件

reviewer は以下を**すべて**検証した上でのみ承認する:

1. **変更箇所の UT**: 新規・変更コードに対するユニットテストが存在し通過
2. **結合テスト**: 変更関連の結合テストが存在し通過
3. **UT リグレッション**: プロジェクト全体テストが通過 (例: `go test ./...`)
4. **lint エラーゼロ**: linter がエラーなしで通過 (例: `golangci-lint run ./...`)

条件未達の場合は implementer に差し戻す。

### 2.6 issue 完了処理

```bash
beads close <issue-id>
```

チームを shutdown し、次の `beads ready` で着手可能な issue に進む。

---

## Phase 3: 集約

### 3.1 ワーキングブランチを機能ブランチへ squash merge

完了した各 issue について:

```bash
git checkout feature/<topic>
git merge --squash feature/<topic>/<issue-id>
git commit -m "feat(<scope>): <issue summary>"
```

### 3.2 クリーンアップ

```bash
# worktree 削除
git worktree remove .claude/worktrees/feature-<topic>-<issue-id>

# ワーキングブランチ削除
git branch -d feature/<topic>/<issue-id>
```

### 3.3 beads 更新

すべての issue が close されていることを確認:

```bash
beads list
```

---

## Phase 4: 完了

### 4.1 MR/PR 作成

リモートの種類を判定して適切なコマンドを使用:

```bash
# GitLab の場合
glab mr create --title "feat: <topic summary>" --description "$(beads list --format markdown)"

# GitHub の場合
gh pr create --title "feat: <topic summary>" --body "$(beads list --format markdown)"
```

MR/PR 本文には:

- epic の概要
- 各 issue の一覧とステータス
- 変更サマリ

### 4.2 epic close

```bash
beads epic close <epic-id>
```

### 4.3 worktree 保持/削除

AskUserQuestion で機能ブランチの worktree を保持するか削除するか確認:

- 保持: MR レビュー中に追加修正が必要な場合に備える
- 削除: `git worktree remove .claude/worktrees/feature-<topic>`

---

## エラーハンドリング

- **beads コマンド失敗**: beads が未インストールの場合は TaskCreate/TaskUpdate で代替
- **worktree 競合**: 既存 worktree がある場合はユーザーに確認
- **マージ競合**: ユーザーに通知し、手動解決を依頼
- **テスト失敗が解消しない**: 3回のフィードバックループ後、ユーザーに判断を仰ぐ
