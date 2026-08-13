---
name: execute-plan
description: Execute an explicitly selected, reviewed implementation plan or short-path task with serial TDD workers, bounded reviews, and local verification; stop before shipping.
---

# Execute Plan

Use only after the user explicitly selected `execute-plan` (or the execute phase of
`execute-and-ship`) for a reviewed plan or reviewed short-path task. Read the
execution contract in [task-execution.md](../../workflows/software_delivery/references/task-execution.md)
and the review policy before dispatching anything.

## Entry and worktree gates

- Validate `context.json`, the approved spec/plan or short-path task, review reports,
  task evidence, and Git evidence on entry and every resume. Missing, stale,
  contradictory, or ahead-of-state evidence stops before a worker dispatch.
- Require the fixed default branch and base commit. Create the worktree only with
  `wt switch --create <branch> --base <default> --no-cd --format=json`; resolve and
  propagate its canonical absolute workdir to every packet and tool.
- Preserve the allowlist, artifact revision, and immutable review snapshot identity;
  stop for hook-trust approval, a non-default base, or protected-contract decisions.

## Serial implementation and review

- Dispatch one fresh Luna Max `worker` per incomplete task, in plan order, with a
  bounded packet (goal, acceptance criteria, owned paths, evidence, validation,
  constraints, stop conditions, and absolute workdir). Workers do not commit,
  push, write externally, or spawn subagents.
- Require `RED -> RED reason -> minimal GREEN -> GREEN confirmation -> limited
  refactor -> GREEN reconfirmation`; permit a TDD exception only when the reviewed
  plan names the target, reason, substitute validation, and reviewer approval.
- After each task, dispatch a fresh read-only `task-reviewer` for separate
  `Spec compliance` and `Simplicity` verdicts. Return important findings to the
  task worker and run scoped re-review; after two failed fixes for one issue, use
  Sol High `debugging`, then a fresh Luna Max worker with its repair conditions.

## Final gate and handoff

- When all tasks are complete, use a fresh Sol `reviewer` (High; XHigh for high
  risk or whenever an important task finding required a fix loop) for the
  fixed-base full diff. Bind its approved snapshot to local
  verification; any snapshot mismatch invalidates both gates.
- Run the recorded validation commands and a feasible real entry point, recording
  failures and unverified scope. On success transition to `LOCAL_COMPLETE` without
  a commit and report `ship-change` as the only optional next phase.
- Follow `~/.codex/review-policy.md`; never infer progress from reports alone.
