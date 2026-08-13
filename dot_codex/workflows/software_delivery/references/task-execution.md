# Execute-plan task execution contract

This reference is the operational contract for the explicit `execute-plan` phase.
It consumes an approved `spec.md` plus `plan.md`, or an approved short-path task
artifact, and ends at `LOCAL_COMPLETE`. It never grants shipping authority and
never creates a commit.

Use the sibling [`spec-and-plan.md`](spec-and-plan.md) for artifact and plan
approval, [`state-recovery.md`](state-recovery.md) for state/CAS recovery,
[`artifact-lifecycle.md`](artifact-lifecycle.md) for artifact ownership, and
[`review-snapshot.md`](review-snapshot.md) for snapshot identity and equality.

## Entry and resume gate

Before a dispatch, validate `context.json` with the state helper and confirm the
recorded phase, artifact revision, execution choice, and immutable identity. The
identity includes the source root, fixed default branch, full base commit, and
artifact paths. The plan review (or short-path preflight) must be passed and the
task's goal, acceptance criteria, owned paths, evidence, validation commands,
constraints, and stop conditions must be readable.

On entry and resume, inspect every referenced artifact and Git evidence. Confirm
that the worktree path and branch are the recorded ones, the base still resolves
to the recorded full commit, and no allowlist-external change is being mistaken
for task output. A missing, stale, contradictory, malformed, or ahead-of-state
artifact or Git record is a hard stop before any worker dispatch. `progress.md`,
reports, and command output are evidence only; `context.json` is the state
authority. Use compare-and-swap revisions for state updates.

Resume from the first incomplete gate. A completed task is never redispatched
(not redispatch):
if its implementation is complete, rerun only its incomplete review; if its
review is complete, rerun only its incomplete verification. Redispatch an
incomplete implementation task once its evidence is revalidated. Do not infer a
completed gate from a report that is newer than the committed context revision.

## Worktree gate

Execution is supported only from the workflow's default branch. Compare the
recorded intended base with the Worktrunk default; a non-default base or branch
is a stop condition. After the execution choice is recorded, run exactly:

```text
wt switch --create <branch> --base <default> --no-cd --format=json
```

Capture and validate the JSON, resolve the selected worktree to an existing
canonical absolute path, and persist that path and branch in `context.json`.
Every worker, reviewer, debugging packet, command, and tool `workdir` receives
that same absolute path. If a project hook requests trust approval, stop and ask
the user; never add `--yes` or bypass the hook. Do not use a fallback worktree
command.

## Serial task worker

Process tasks strictly in plan order, one task at a time. For each incomplete task, start one fresh
Luna Max `worker` and provide one bounded packet containing the task goal,
acceptance criteria, exact owned paths, dependency/evidence paths, validation
commands, constraints, stop conditions, fixed absolute workdir, and current
artifact revision. The worker stays within owned paths, preserves unrelated user
changes, and does not commit, push, write external systems, or spawn subagents.

For an observable behavior change, require this sequence and record each result:

```text
RED -> verify the expected RED reason -> minimal GREEN -> verify GREEN
     -> limited refactor -> verify GREEN again
```

The RED test must fail for the documented reason before implementation. A
limited refactor only removes duplication or improves naming inside the owned
change; it cannot add behavior or future-facing abstraction. A docs, generated
artifact, pure configuration, or other non-behavioral task may bypass RED only
when the approved plan explicitly records the target, why RED is impossible, an
alternative validation command, and reviewer approval: this is the approved TDD exception.
Never invent a TDD exception at execution time.

## Task review and fix loop

After the worker reports completion and focused validation passes, start a fresh
read-only `task-reviewer` instance separate from the worker and from any
preflight reviewer. The normal reviewer is Luna Max/Max. It must return separate
`Spec compliance` and `Simplicity` verdicts for the same bounded task packet and
evidence; it must not edit files or rerun trusted commands. Use Sol High for a
task spanning multiple components, complex control flow, high-risk state, or
insufficient evidence.

An important finding returns to the task worker with the exact scenario, impact,
primary evidence, smallest fix or verification, and the changed delta. Re-run
focused validation and a scoped re-review (a scoped fresh review) before starting
the next task.
Keep a per-issue failed-fix count. When the same issue has two failed fixes, stop
the worker loop and dispatch read-only Sol High `debugging` to establish root
cause and repair conditions. Then dispatch a fresh Luna Max worker with only that
bounded repair packet and repeat the review gate. An unresolved important finding,
scope expansion, protected-contract decision, or untrusted validation stops the
workflow.

## Final review, snapshot, and local verification

After every task is reviewed, start a fresh Sol `reviewer` (normally High; use
XHigh for protected contracts, security, migration, concurrency/distribution,
multiple services, insufficient evidence, or whenever an important task finding required a fix loop).
It reviews the complete allowlisted diff from the fixed merge-base and uses only
the applicable lenses in
`~/.codex/review-policy.md`. A task reviewer cannot serve as this final reviewer.
The verdict is `APPROVED`, `CHANGES_REQUIRED`, or `USER_DECISION_REQUIRED`.

Compute the immutable `review_snapshot_id` (the review snapshot identity) with the Task 4 snapshot helper using
the full base commit and the intended worktree tree. Bind final review and local
verification to that same snapshot. Any changed content, mode, deletion,
allowlist, base, or external-dirty preflight invalidates both gates and requires
their rerun; never reuse a report for a different snapshot.

After an `APPROVED` final review, run every recorded validation command and a
feasible real entry point in the fixed absolute workdir. Record exact commands,
success, failure history, and unverified scope in the verification artifact and
advance state only through `context.json`. A failure returns to its owning task,
review, or verification gate; it does not justify skipping a gate.

On success, record the matching snapshot and transition to `LOCAL_COMPLETE`.
`execute-plan` selection means local completion only: no commit (never a commit),
and do not stage, push,
open/modify an MR, merge, release, tag, or perform external writes. Report the
result and identify explicit `ship-change` as the next phase (the next optional
phase). The
`execute-and-ship` composite may use this completed handoff only after its
separate shipping authorization is recorded.

## Stop and recovery conditions

Stop before dispatch for a non-default base, unapproved Worktrunk hook, missing
or inconsistent artifact/Git evidence, stale revision, snapshot mismatch,
unresolved important finding, protected-contract or security decision, scope
expansion, or validation that cannot be trusted. Keep the worktree and artifacts
available for investigation. On a later resume, revalidate the recorded context
and Git state, preserve completed task history, and continue only at the first
incomplete gate; never infer progress from partially written files or reports.
