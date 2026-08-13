# Post-merge cleanup handoff

Post-merge cleanup runs only after the user explicitly requests it and the
forge confirms that the workflow's merge request is merged.  Before removing
anything, record the exact branch, canonical worktree path, and artifact
directory from schema-v1 `context.json`.

Only the worktree — and the local branch Worktrunk deletes with it — is
removed.  The artifact under `.aidocs/workflows/<workflow-id>/` holds the spec,
plan, review, and verification record and is still referenced after the merge,
so it is kept.

## Salvaging worktree-only records

Files that exist only inside the worktree disappear with it.  Copy them into
the parent repository's `.aidocs/workflows/<workflow-id>/` *before* removal:
the worktree-private git dir's `harness-evidence.jsonl` (resolved with `git -C
<worktree> rev-parse --path-format=absolute --git-dir`, appended to the
artifact's `evidence.jsonl` without duplicating existing lines), and any
verification logs or outputs that never landed in a commit.  Stop and report
if something cannot be salvaged.

## Worktrunk removal

List the intended resources first, then run this exact command from the
repository's primary worktree.  Save stdout without changing the command or
adding flags:

```text
wt remove --foreground --format=json <branch> > wt-remove.json
```

The command must not use `--force`, `-D` (or `--force-delete`), `--no-hooks`,
or `--yes` (or `-y`).  A dirty worktree, an unmerged or moved branch, or an
unapproved hook is a stop condition.  Do not fall back to `git worktree
remove`, branch deletion, `rm`, or another destructive cleanup command.

If the local default branch has not yet absorbed the merge, Worktrunk reports
the branch as unmerged, removes the worktree, and keeps the branch.  Advance
the parent repository's default branch with `git fetch` and run the same
command again.  Never reach for `-D`.  A branch that genuinely is not in the
default branch's history is a stop condition.

## Result gate

Confirm the removal against Git, not against the saved JSON:

```text
git worktree list                 # the canonical worktree path is gone
git branch --list <branch>        # the output is empty
```

Worktrunk's JSON schema changes between versions — v0.71.0 returns
`{"branch","branch_checked_out_at","branch_deleted","kind","path"}` and splits
worktree removal and branch deletion into separate records from separate runs —
so no helper validates it and its shape is never the deletion verdict.  Save
`wt-remove.json` into the artifact as evidence only.

Terminal success requires both checks.  Anything else is nonterminal: a
retained, unmerged, or checked-out branch, a deferred or not_attempted removal,
invalid JSON, or a mismatch with `context.json` keeps the worktree and artifact
on hold for investigation or a later retry, and does not delete anything.  Do
not escalate to a forced removal.

## Terminal state

Only after both Git checks pass may the controller use `workflow_state.py` to
transition the context to `WT_REMOVE` with the expected artifact revision, and
set `workspace.worktree_path` to null.  `WT_REMOVE` is this phase's terminal
state: do not advance to `ARTIFACT_REMOVE` and do not invoke
`workflow_artifact.py remove`.  That edge remains in the state machine only for
a separate, explicit user request to delete a workflow's records.  Remote
branch deletion is outside this handoff and is not performed unless separately
authorized by the forge workflow.
