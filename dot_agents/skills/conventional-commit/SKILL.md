---
name: conventional-commit
description: Conventional Commits形式のコミットメッセージ作成・種類選定、submodule のコミット先判断 (サブモジュール vs 親リポ)、worktree CWD 検証時に使用。git commit / worktree / submodule の文脈で発火。
ecc-imports:
  - upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
    upstream-path: skills/git-workflow/SKILL.md
    sections-merged:
      - "Commit Messages"
    conflicts:
      - "When to Activate"
      - "Branching Strategies"
      - "Merge vs Rebase"
      - "Pull Request Workflow"
      - "What"
      - "Why"
      - "How"
      - "Testing"
      - "Screenshots (if applicable)"
      - "Checklist"
      - "Conflict Resolution"
      - "Branch Management"
      - "Release Management"
      - "Git Configuration"
      - "Common Workflows"
      - "Git Hooks"
      - "Anti-Patterns"
      - "Quick Reference"
    imported-at: 2026-04-27T00:00:00+09:00
---

# Conventional Commitsガイド

## コンテキスト

- Git Status !`git status`
- Git Diff !`git diff --cached`
- Git Log !`git log --oneline -20`

## 目的

- 変更内容を一貫した形式で伝える。
- 自動的なCHANGELOG生成やリリースノート作成を支援する。

## 形式

```
<type>(<scope>): <subject>
```

- `<scope>` は任意。対象が明確なら指定し、迷う場合は省略する。
- 破壊的変更はフッターで明示する。

### 破壊的変更

```
BREAKING CHANGE: legacy auth endpoints are removed
```

## type一覧

`feat` / `fix` / `docs` / `style` (フォーマットや空白などの修正、動作変更なし) / `refactor` / `perf` / `test` / `build` (ビルドや依存関係) / `ci` / `chore` (雑務やメタ作業) / `revert`。用例は下記「#### Types」テーブルを参照。

## 英語コミットメッセージのルール

- `<subject>` は命令形で書く。
- 先頭は小文字にする。
- 末尾にピリオドを付けない。
- emoji を使わない。
- AI attribution、`Co-authored-by`、その他の生成元署名を付けない。

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
- 破壊的変更は`BREAKING CHANGE:` で明示している。
- コミットメッセージは原則英語とする。ただし、過去のメッセージが日本語の場合は一貫性を優先しても良い。

## ECC 由来: skills/git-workflow/SKILL.md

> ECC base commit `4e66b2882da9afb9747468b08a253ca2f09c85f3` の `skills/git-workflow/SKILL.md` から `Commit Messages` セクションのみ採用。
> 残り 18 H2（Branching Strategies, Merge vs Rebase, PR Workflow 等）は本 skill のスコープ外につき conflicts として記録（採用せず）。git workflow 全般は別 skill / 別 spec で扱う。
> Conventional Commits Format / Types は既存の §形式 / §type一覧 と内容が重複。**英語例の Type 一覧、Good vs Bad Examples、`.gitmessage` Template が ECC 由来の追加価値**。

### Commit Messages

#### Conventional Commits Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

#### Types

| Type | Use For | Example |
|------|---------|---------|
| `feat` | New feature | `feat(auth): add OAuth2 login` |
| `fix` | Bug fix | `fix(api): handle null response in user endpoint` |
| `docs` | Documentation | `docs(readme): update installation instructions` |
| `style` | Formatting, no code change | `style: fix indentation in login component` |
| `refactor` | Code refactoring | `refactor(db): extract connection pool to module` |
| `test` | Adding/updating tests | `test(auth): add unit tests for token validation` |
| `chore` | Maintenance tasks | `chore(deps): update dependencies` |
| `perf` | Performance improvement | `perf(query): add index to users table` |
| `ci` | CI/CD changes | `ci: add PostgreSQL service to test workflow` |
| `revert` | Revert previous commit | `revert: revert "feat(auth): add OAuth2 login"` |

#### Good vs Bad Examples

```
# BAD: Vague, no context
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "WIP"

# GOOD: Clear, specific, explains why
git commit -m "fix(api): retry requests on 503 Service Unavailable

The external API occasionally returns 503 errors during peak hours.
Added exponential backoff retry logic with max 3 attempts.

Closes #123"
```

#### Commit Message Template

Create `.gitmessage` in repo root:

```
# <type>(<scope>): <subject>
#
# Types: feat, fix, docs, style, refactor, test, chore, perf, ci, revert
# Scope: api, ui, db, auth, etc.
# Subject: imperative mood, no period, max 50 chars
#
# [optional body] - explain why, not what
# [optional footer] - Breaking changes, closes #issue
```

Enable with: `git config commit.template .gitmessage`

## サブモジュールのコミット規約

サブモジュールを含むリポジトリで作業する場合、**今どちらのリポジトリでコミットすべきか**を意識する。

| やりたいこと | コミット場所 |
|---|---|
| サブモジュール内のコードを変更した | サブモジュールディレクトリ内で `git commit` |
| サブモジュールのポインタ (参照先 commit) を更新したい | 親リポジトリのルートで `git add <submodule-path>` → `git commit` |

**よくある間違い**:
- 親リポのサブモジュールポインタを更新したいのに、サブモジュールディレクトリ内に入ってコミットしてしまう
- 逆に、サブモジュール内のコード変更を親リポからコミットしようとしてしまう

**確認手順**: `pwd` → `git rev-parse --show-toplevel` でどのリポジトリにいるか確認してからコミット。

## Worktree ディレクトリ検証

Git worktree で作業する場合、ファイル編集前に必ず以下を確認する。

1. ユーザーが worktree での作業を指示した場合、最初の Edit/Write の前に `pwd` で現在のディレクトリを確認する
2. CWD が意図した worktree パスと一致しない場合、編集を開始せずユーザーに確認する
3. メインリポジトリのパスで worktree 向けの編集を行ってはならない

**確認すべきタイミング**: セッション開始時に worktree パス言及 / `wt switch` 等の直後 / 別 worktree への切替時。

**確認不要**: ユーザーが明示的にメインリポでの作業を指示 / セッション CWD が最初から worktree 内 (gitStatus で確認可能)。

## /ECC 由来: skills/git-workflow/SKILL.md
