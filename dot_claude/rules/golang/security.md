---
paths:
  - "**/*.go"
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: rules/golang/security.md
  imported-at: 2026-04-27T00:00:00+09:00
  adapted: false
---

---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
# Go Security

> This file extends [common/security.md](../common/security.md) with Go specific content.

## Secret Management

```go
apiKey := os.Getenv("OPENAI_API_KEY")
if apiKey == "" {
    log.Fatal("OPENAI_API_KEY not configured")
}
```

## Security Scanning

- Use **gosec** for static security analysis:
  ```bash
  gosec ./...
  ```

## Context & Timeouts

Always use `context.Context` for timeout control:

```go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
```
