# Immutable review snapshot

`review_snapshot.py` binds review, local verification, and later staging to one
allowlisted intended tree. It reads Git metadata and the selected worktree or
index; it never writes the index.

```text
python review_snapshot.py \
  --repo ROOT \
  --base-commit FULL_COMMIT \
  --allowlist-json '{"version":1,"paths":["path/to/file"]}' \
  --source worktree|index \
  --output MANIFEST
```

The allowlist is version `1` and contains normalized repository-relative file
paths. Duplicate paths, `..` escapes, absolute paths, trailing separators,
symlinked parents, and `.git` metadata paths are rejected. A full resolved Git
commit ID is required; an abbreviated commit is rejected.

## Manifest and identity

The output manifest is written atomically and has this exact shape:

```json
{
  "base_commit": "<full lowercase commit id>",
  "paths": [
    {
      "content_sha256": "<raw content SHA-256 or null>",
      "mode": "100644|100755|120000|040000|160000 or null",
      "path": "repository/relative/path",
      "state": "present|deleted|absent"
    }
  ]
}
```

Entries are sorted by normalized path. `present` records the selected final
tree's mode and raw bytes (symlinks hash their link target); `deleted` retains
the removed base entry's mode and content hash where it has a blob; `absent`
means neither the base tree nor the selected tree contains the path.

The snapshot ID is `sha256:<hex>` over the UTF-8 bytes of the manifest encoded
as canonical JSON (`sort_keys=True`, compact separators, no trailing newline).
The source selector is not part of the manifest, so an equivalent worktree and
index tree produce the same ID. Changing the base commit, allowlisted content,
mode, or deletion changes the ID.

## Preflight and equality gate

Standard output is one JSON object containing the ID and preflight result:

```json
{
  "preflight": {
    "external_dirty_paths": [],
    "external_staged_paths": [],
    "shipping_blocked": false
  },
  "review_snapshot_id": "sha256:<hex>"
}
```

Dirty or staged paths outside the allowlist are reported separately and are
excluded from the identity. They still block shipping. In `index` mode, any
external staged path is a hard error (and no manifest is replaced); external
unstaged paths remain observable as a blocking preflight. The requested
manifest is replaced only after all validation and hashing succeeds, using a
same-directory temporary file and `os.replace`.

Immediately before staging and immediately before committing, recompute the
snapshot with the same full base commit and allowlist. Proceed only when the
new ID exactly equals the ID recorded by final review and local verification;
otherwise invalidate those gates and rerun them for the changed snapshot.
