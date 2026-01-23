# Output Patterns

Skillsが安定した高品質出力を出せるよう、以下のパターンを使う。

## Template Pattern

出力フォーマット用のテンプレートを与える。厳密さは要件に合わせる。

**厳密な要件 (APIレスポンスやデータ形式など):**

```markdown
## Report structure

ALWAYS use this exact template structure:

# [Analysis Title]

## Executive summary

[One-paragraph overview of key findings]

## Key findings

- Finding 1 with supporting data
- Finding 2 with supporting data
- Finding 3 with supporting data

## Recommendations

1. Specific actionable recommendation
2. Specific actionable recommendation
```

**柔軟なガイド (適応が必要な場合):**

```markdown
## Report structure

Here is a sensible default format, but use your best judgment:

# [Analysis Title]

## Executive summary

[Overview]

## Key findings

[Adapt sections based on what you discover]

## Recommendations

[Tailor to the specific context]

Adjust sections as needed for the specific analysis type.
```

## Examples Pattern

出力品質が例に依存する場合は、入出力のペアを用意する。

```markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```

feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:
```

fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation

```

Follow this style: type(scope): brief description, then detailed explanation.
```

例は、説明だけよりも望ましい文体や粒度を正確に伝えられる。
