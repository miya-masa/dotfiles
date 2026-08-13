# Workflow state and recovery

`context.json` is the only machine-readable state authority for a software-
delivery workflow. Reports, `progress.md`, and command output are evidence;
they must not advance a workflow by themselves.

## Schema v1

The document contains these required objects:

- `identity`: `schema_version` (`1`), `workflow_id`, `source_root`,
  `artifact_root`, `default_branch`, and `base_commit`.
- `workspace`: nullable `worktree_path` and `branch`.
- `state`: `phase`, nullable `stopped_from`, and non-negative
  `artifact_revision`.
- `authorization`: `shipping_authorized`.
- `artifacts`: `spec_path`, nullable `plan_path`, `tasks_path`, `reviews_path`,
  and `verification_path`.
- `execution`: task records, gate records, nullable execution `choice`, and
  nullable `review_snapshot_id`.
- `shipping`: nullable `commit`, `push`, `mr`, and `ci` status values.

Identity is immutable after initialization. The state graph includes
`DISCOVERY` through `ARTIFACT_REMOVE`, the short-path phases
`SHORT_TASK_DRAFT` and `SHORT_TASK_PREFLIGHT`, plus `DEBUGGING` and
`USER_DECISION_REQUIRED`; it has no `STOPPED` phase. The short-path edges are
`DISCOVERY -> SHORT_TASK_DRAFT`, `SHORT_TASK_DRAFT -> SHORT_TASK_PREFLIGHT`,
and `SHORT_TASK_PREFLIGHT -> EXECUTION_CHOICE`, with redraft returns to
`SHORT_TASK_DRAFT`, normative gaps returning to `DISCOVERY`, and blocker edges
to `USER_DECISION_REQUIRED`. An external blocker uses `stop`, which records
the previous phase in `state.stopped_from`, and `resume` restores that phase.
A user-decision state without `stopped_from` is not resumable; resolve it
through the appropriate normative or controller gate.

## CLI contract

All commands require `--context <path>`:

```text
workflow_state.py validate --context context.json
workflow_state.py transition --context context.json \
  --expected-revision N --to PHASE [--patch-json JSON_OBJECT]
workflow_state.py invalidate-normative --context context.json \
  --expected-revision N
workflow_state.py stop --context context.json --expected-revision N \
  --reason "external blocker"
workflow_state.py resume --context context.json --expected-revision N
```

Every successful mutation is a compare-and-swap: the supplied revision must
equal `state.artifact_revision`, and the resulting revision is exactly one
higher. Invalid JSON, missing fields, an invalid transition, an immutable
identity change, or a stale revision exits nonzero and leaves the original
bytes untouched.

`invalidate-normative` moves to `SPEC_REVIEWS`, removes `plan_path`, clears
the active `execution.tasks` map, clears plan and downstream gate values,
clears execution choice and snapshot, revokes shipping authorization, and
resets shipping statuses. Active task IDs must not survive into a replacement
plan. Audit history belongs in append-only `progress.md` or a separate
history/audit field; such separate fields are not modified by invalidation.

## Atomic commit point and recovery

For a mutation, the helper serializes the complete next context to a uniquely
named temporary file in the context's directory, flushes and `fsync`s that
file, and then calls `os.replace` onto `context.json`. The successful replace
is the commit point. A failed write or interruption before replace removes
the temporary file and leaves the previous context byte-for-byte unchanged.

The complete load, revision compare, operation, and replace sequence is held
under an advisory `fcntl.flock` exclusive lock on the containing directory
inode. Locking the directory (rather than the replaced context inode) keeps
the lock stable across `os.replace`; no lock file is created or deleted. A
second writer therefore reads the newly committed revision after waiting and
fails the compare-and-swap as stale.

On resume after interruption, read and validate `context.json`, inspect the
recorded artifact and Git evidence, and trust only the last atomically
committed revision. Never infer a later state from a partially written temp
file or from an evidence report that is ahead of the context.
