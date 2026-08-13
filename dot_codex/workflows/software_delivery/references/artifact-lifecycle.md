# Workflow artifact lifecycle

`workflow_artifact.py` owns only the project-local directory
`.aidocs/workflows/<workflow-id>/`.  It uses Python's standard library and the
repository's Git CLI; missing or unwritable Git metadata is a hard error.

## Identity and layout

`new-id [slug]` normalizes the optional slug to lowercase ASCII and hyphens,
limits it to 38 characters, and appends the current UTC second plus eight
random hexadecimal characters.  The result is at most 63 characters and
matches `[a-z0-9][a-z0-9-]{0,62}`.  `init` rejects an existing or colliding
workflow directory and rejects traversal, absolute, malformed, or symlinked
paths.

```text
.aidocs/workflows/<workflow-id>/
├── spec.md
├── plan.md
├── progress.md
├── context.json
├── tasks/
├── reviews/
└── verification.md
```

The initializer records the canonical project root, artifact root, Git
default branch, and full base commit in the schema-v1 `context.json`.  The
initial state is `DISCOVERY` with revision `0`, no worktree, no shipping
authorization, empty task history, and pending `spec_review`.  The sibling
`workflow_state.py validate` implementation remains the schema authority.

## Ignore ownership

Before creating an artifact, the helper runs `git check-ignore` for
`.aidocs/`.  If the project does not already ignore it, the exact rule
`/.aidocs/` is appended once to the repository-local `.git/info/exclude`.
Existing bytes are preserved, repeated initialization is idempotent, and the
tracked project `.gitignore` is never edited.  A symlinked or unavailable Git
metadata path is rejected rather than redirected to another location.

## Terminal removal

`remove` is fail-closed.  It verifies the canonical project root, a single
non-symlink direct child workflow path, and the matching `context.json`
identity.  The context must be schema-valid, in phase `ARTIFACT_REMOVE`, and
have the exact caller-supplied `--expected-revision`; an optional
`--phase ARTIFACT_REMOVE`/`--authorize ARTIFACT_REMOVE` is also checked when
provided.  Any mismatch leaves the artifact untouched.  Only the one verified
workflow directory is removed, never `.aidocs/`, another workflow, or a
symlink target.

```text
workflow_artifact.py new-id [slug] [--project-root ROOT]
workflow_artifact.py init --project-root ROOT --workflow-id ID
workflow_artifact.py remove --project-root ROOT --workflow-id ID \
  --expected-revision N [--phase ARTIFACT_REMOVE] [--context PATH]
```

The optional `--default-branch` and `--base-commit` flags on `init` override
Git discovery.  Removal is the final handoff after the state CLI has reached
`ARTIFACT_REMOVE`; this helper does not advance or rewrite `context.json`.
