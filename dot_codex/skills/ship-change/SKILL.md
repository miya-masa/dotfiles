---
name: ship-change
description: Ship an explicitly authorized, locally complete change through one commit, push, MR, and in-scope CI; stop before merge or release.
---

# Ship Change

Use only after explicit `ship-change` selection, or an execute-and-ship handoff
that records shipping authorization. The input must be `LOCAL_COMPLETE`
with passed final review and local verification; ordinary implementation never
authorizes shipping.

## Entry and resume gates

- Validate `context.json`, fixed default branch/base, artifact revision, allowlist,
  review/verification evidence, `review_snapshot_id`, and every recorded commit,
  remote, MR, and CI status on entry or resume. Missing, stale, contradictory,
  or snapshot-mismatched evidence stops.
- Before staging or commit, the controller inspects repository status, intended
  base/head, allowlist, and staged tree for secrets, local paths, and internal
  workflow artifacts. No scanner is invented: suspected contamination or
  unavailable evidence fails closed; refuse external dirty or staged paths.
- immediately before staging, recompute the Task 4 `review_snapshot.py` identity
  and preflight; after staging recompute against the index, then recompute against
  the index immediately before commit with no intervening change. Refuse external
  dirty or staged paths. Stage only the allowlist and require reviewed, verified,
  and staged identities to be exactly equal; any mismatch invalidates review and
  verification and stops.

## Controller shipping sequence

The controller makes one logical commit only after the equality gate, then pushes
the recorded branch and opens an MR whose target is the fixed Worktrunk default
branch. On resume, reuse validated commit, remote, and MR evidence; never
duplicate push or duplicate MR creation. Monitor CI and apply only in-scope
implementation fixes through the same review/verification/snapshot gates before
re-pushing. Use escalation for an external blocker such as a CI/runner failure
instead of guessing.

This skill never merges (no merge), releases, tags, changes production, handles
credentials or permission changes, or accepts a local-merge override. Stop for
unauthorized shipping, snapshot/commit/remote/MR/CI evidence mismatch, external
dirty state, scope expansion, protected contract decisions, or external failure.

Read [task-execution.md](../../workflows/software_delivery/references/task-execution.md),
[review-snapshot.md](../../workflows/software_delivery/references/review-snapshot.md),
[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md),
and `~/.codex/review-policy.md` before acting. A ready MR is the terminal result
of this phase; explicitly suggest `post-merge-cleanup` only after a later merge.
