---
paths:
  - "**/*.go"
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: rules/golang/hooks.md
  imported-at: 2026-04-27T00:00:00+09:00
  adapted: false
---

---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
# Go Hooks

> This file extends [common/hooks.md](../common/hooks.md) with Go specific content.

## PostToolUse Hooks

Configure in `~/.claude/settings.json`:

- **gofmt/goimports**: Auto-format `.go` files after edit
- **go vet**: Run static analysis after editing `.go` files
- **staticcheck**: Run extended static checks on modified packages
