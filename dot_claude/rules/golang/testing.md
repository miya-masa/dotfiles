---
paths:
  - "**/*_test.go"
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: rules/golang/testing.md
  imported-at: 2026-04-27T00:00:00+09:00
  adapted: false
---

---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
# Go Testing

> This file extends [common/testing.md](../common/testing.md) with Go specific content.

## Framework

Use the standard `go test` with **table-driven tests**.

## Race Detection

Always run with the `-race` flag:

```bash
go test -race ./...
```

## Coverage

```bash
go test -cover ./...
```

## Reference

See skill: `golang-testing` for detailed Go testing patterns and helpers.
