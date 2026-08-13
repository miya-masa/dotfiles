---
name: post-merge-cleanup
description: After explicit authorization and a confirmed merged MR, safely remove the workflow-owned Worktrunk worktree while keeping the artifact.
---

# Post-Merge Cleanup

Run only after an explicit user request. Confirm the forge MR is merged and
`context.json` proves exact branch, canonical worktree, artifact root, ownership,
and the expected workflow. List those resources before any removal; validate
state and evidence on entry or resume.

Remove only the worktree (and the local branch Worktrunk deletes with it). The
artifact under `.aidocs/workflows/<workflow-id>/` is the sole record of what was
decided and verified, so it is kept. Salvage anything that exists only inside the
worktree into the artifact before removal.

From the repository's primary worktree, run exactly:

```text
wt remove --foreground --format=json <branch>
```

Save its JSON without `--force`, `-D`, `--no-hooks`, `--yes`, or fallback removal
commands. A dirty/unmerged/moved branch, hook trust request, or ownership
mismatch stops and retains everything.

Confirm the removal against Git, not against that JSON: `git worktree list` must
no longer show the canonical path and `git branch --list <branch>` must be empty.
Worktrunk's schema changes between versions, so a saved result is evidence only
and never the deletion verdict. Anything else — a retained or unmerged branch, a
deferred or not_attempted removal, invalid JSON, or a mismatch — is nonterminal,
keeps everything on hold, and does not delete anything. Only a confirmed removal
transitions to `WT_REMOVE` via `workflow_state.py` with the expected revision.
Do not advance to `ARTIFACT_REMOVE` or invoke Task 3's `workflow_artifact.py
remove`; `WT_REMOVE` is this phase's terminal state.

remote branch deletion is outside this handoff; do not delete it. On successful
worktree removal, report a terminal state and no next skill; never run cleanup
before merge or infer deletion from a report alone. Read
[post-merge-cleanup.md](../../workflows/software_delivery/references/post-merge-cleanup.md),
[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md),
and `~/.codex/review-policy.md`.
