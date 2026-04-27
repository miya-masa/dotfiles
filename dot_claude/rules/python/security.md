---
paths:
  - "**/*.py"
  - "**/*.pyi"
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: rules/python/security.md
  imported-at: "2026-04-27T00:00:00+09:00"
  adapted: false
---

# Python Security

> This file extends [common/security.md](../common/security.md) with Python specific content.

## Secret Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing
```

## Security Scanning

- Use **bandit** for static security analysis:
  ```bash
  bandit -r src/
  ```

## Reference

See skill: `django-security` for Django-specific security guidelines (if applicable).
