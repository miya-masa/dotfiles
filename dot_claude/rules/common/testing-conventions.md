---
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: rules/common/testing.md
  imported-at: 2026-04-27T00:00:00+09:00
  adapted: true
  adapted-for: []
---

# Testing Conventions（言語非依存）

ECC `rules/common/testing.md` から AAA パターンとテスト命名規約のみ抽出した版。TDD サイクル / カバレッジ目標 / E2E 必須要求は除外（既存スキルとの棲み分けのため）。

## 棲み分け

- TDD サイクル（RED → GREEN → REFACTOR）: `tdd` skill が責務を持つ
- カバレッジ目標（80% 等）: `testing-golang` skill / Testing Rules（CLAUDE.md）が責務を持つ
- E2E 必須要求: プロジェクト判断（本 rule では指定しない）

## Test Structure (AAA Pattern)

Prefer Arrange-Act-Assert structure for tests:

```typescript
test('calculates similarity correctly', () => {
  // Arrange
  const vector1 = [1, 0, 0]
  const vector2 = [0, 1, 0]

  // Act
  const similarity = calculateCosineSimilarity(vector1, vector2)

  // Assert
  expect(similarity).toBe(0)
})
```

各言語版（Go の `testing-golang` skill、Python の `python-testing` skill 等）でも同等の AAA 構造が推奨される。

## Test Naming

Use descriptive names that explain the behavior under test:

```typescript
test('returns empty array when no markets match query', () => {})
test('throws error when API key is missing', () => {})
test('falls back to substring search when Redis is unavailable', () => {})
```

命名は **「動詞句で観察可能な振る舞いを表す」** ことを優先。仕様の表現として読めるテスト名にする。
