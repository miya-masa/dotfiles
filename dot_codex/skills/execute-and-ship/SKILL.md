---
name: execute-and-ship
description: Execute a reviewed plan and, with explicit shipping authorization, continue through MR-ready CI without merging.
---

# Execute and Ship

Use only when the user explicitly selects this composite for a reviewed plan or
reviewed short-path task. Record `shipping_authorized: true` before dispatch;
this is comprehensive authority for the bounded commit, push, MR, and in-scope
CI loop, not for any other external action.

The composite performs only:

```text
execute-plan -> ship-change
```

First run `execute-plan` with its serial TDD, task-review, final-review, snapshot,
and local verification gates. Do not commit during execution. On matching
`LOCAL_COMPLETE`, hand off without another shipping question to `ship-change`,
which revalidates evidence and continues through MR-ready CI. Resume each phase
from its first incomplete gate and do not duplicate completed external writes.

This skill does not include discovery or planning, and it never authorizes merge,
post-merge cleanup, release, tag, production, credentials, permissions, or scope
expansion. Validate `context.json` and stop on missing authorization, changed snapshot, protected-contract
decision, external CI/runner failure, or any evidence mismatch. Read the
[task-execution.md](../../workflows/software_delivery/references/task-execution.md),
[review-snapshot.md](../../workflows/software_delivery/references/review-snapshot.md),
and [state-recovery.md](../../workflows/software_delivery/references/state-recovery.md)
contracts before dispatch.
