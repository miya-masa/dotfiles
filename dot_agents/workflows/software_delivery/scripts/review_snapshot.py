#!/usr/bin/env python3
"""Compute an immutable, allowlisted Git review snapshot.

The snapshot is deliberately based on the intended tree selected by the
caller (the worktree or the index), rather than on Git's change provenance.
Only the Python standard library and the Git CLI are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


class SnapshotError(Exception):
    """An invalid snapshot request or unavailable Git state."""


class _BaseEntry:
    __slots__ = ("mode", "object_type", "object_id")

    def __init__(self, mode: str, object_type: str, object_id: str) -> None:
        self.mode = mode
        self.object_type = object_type
        self.object_id = object_id


class SnapshotResult:
    """The canonical manifest, identity, and shipping preflight."""

    __slots__ = ("manifest", "review_snapshot_id", "preflight")

    def __init__(
        self,
        manifest: dict[str, Any],
        review_snapshot_id: str,
        preflight: dict[str, Any],
    ) -> None:
        self.manifest = manifest
        self.review_snapshot_id = review_snapshot_id
        self.preflight = preflight


def _git_bytes(root: Path, *args: str) -> bytes:
    environment = os.environ.copy()
    # Snapshot reads must never take Git's optional index lock or refresh the
    # stat cache as a side effect of commands such as ``status``.
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise SnapshotError(f"Git metadata unavailable: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SnapshotError(detail or "Git command failed")
    return result.stdout


def _git_text(root: Path, *args: str) -> str:
    return _git_bytes(root, *args).decode("utf-8", "replace").strip()


def repository_root(repo: Path | str) -> Path:
    """Return the canonical root for a repository or repository subdirectory."""

    requested = Path(repo).expanduser()
    try:
        requested = requested.resolve(strict=True)
    except OSError as exc:
        raise SnapshotError(f"repository is unavailable: {exc}") from exc
    if not requested.is_dir():
        raise SnapshotError("repository must be a directory")
    try:
        discovered = Path(_git_text(requested, "rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as exc:
        raise SnapshotError(f"Git repository root is unavailable: {exc}") from exc
    if not discovered.is_dir():
        raise SnapshotError("Git repository root is unavailable")
    return discovered


def _normalize_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise SnapshotError("allowlist paths must be non-empty strings")
    if "\x00" in value or "\\" in value:
        raise SnapshotError(f"allowlist path is not a normalized repository path: {value!r}")
    if value.endswith("/"):
        raise SnapshotError(f"allowlist path must name one path: {value!r}")
    if value.startswith("/"):
        raise SnapshotError(f"allowlist path escapes the repository: {value!r}")
    parts = value.split("/")
    if any(part == ".." for part in parts):
        raise SnapshotError(f"allowlist path escapes the repository: {value!r}")
    normalized_parts = [part for part in parts if part not in ("", ".")]
    if not normalized_parts:
        raise SnapshotError("allowlist path must not be empty")
    if any(part == ".git" for part in normalized_parts):
        raise SnapshotError("allowlist must not include Git metadata paths")
    normalized = "/".join(normalized_parts)
    # PurePosixPath is used only as a final lexical check; filesystem
    # resolution is intentionally not used because a final symlink is a valid
    # snapshot entry.
    if str(PurePosixPath(normalized)) != normalized:
        raise SnapshotError(f"allowlist path is not normalized: {value!r}")
    return normalized


def normalize_allowlist(value: Mapping[str, Any] | str) -> list[str]:
    """Validate and normalize an allowlist-v1 object or JSON string."""

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError) as exc:
            raise SnapshotError(f"allowlist JSON is invalid: {exc}") from exc
    else:
        parsed = value
    if not isinstance(parsed, dict):
        raise SnapshotError("allowlist must be a JSON object")
    version = parsed.get("version")
    if isinstance(version, bool) or version != 1:
        raise SnapshotError("allowlist version must be 1")
    paths = parsed.get("paths")
    if not isinstance(paths, list):
        raise SnapshotError("allowlist paths must be an array")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in paths:
        path = _normalize_path(value)
        if path in seen:
            raise SnapshotError(f"allowlist contains duplicate path: {path}")
        seen.add(path)
        normalized.append(path)
    return sorted(normalized)


def _resolve_base_commit(root: Path, supplied: str) -> str:
    if not isinstance(supplied, str) or not supplied or any(
        character not in "0123456789abcdefABCDEF" for character in supplied
    ):
        raise SnapshotError("base commit must be a full hexadecimal object id")
    # A short object id is deliberately not accepted.  Resolving and comparing
    # the exact supplied bytes also rejects a 40-character ref that happens to
    # resolve to another object.
    if len(supplied) < 40:
        raise SnapshotError("base commit must be full, not abbreviated")
    try:
        resolved = _git_text(
            root,
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{supplied}^{{commit}}",
        )
    except SnapshotError as exc:
        raise SnapshotError(f"cannot resolve full base commit: {exc}") from exc
    if resolved.lower() != supplied.lower():
        raise SnapshotError("base commit must be the full resolved commit id")
    return resolved.lower()


def _path_bytes(path: str) -> bytes:
    try:
        return os.fsencode(path)
    except UnicodeEncodeError as exc:
        raise SnapshotError(f"allowlist path cannot be represented safely: {path!r}") from exc


def _parse_ls_tree(data: bytes) -> dict[bytes, _BaseEntry]:
    entries: dict[bytes, _BaseEntry] = {}
    for record in data.split(b"\0"):
        if not record:
            continue
        try:
            header, path = record.split(b"\t", 1)
            mode, object_type, object_id = header.split(b" ", 2)
        except ValueError as exc:
            raise SnapshotError("Git returned an invalid base tree entry") from exc
        try:
            entries[path] = _BaseEntry(
                mode.decode("ascii"),
                object_type.decode("ascii"),
                object_id.decode("ascii"),
            )
        except UnicodeDecodeError as exc:
            raise SnapshotError("Git returned an invalid base tree entry") from exc
    return entries


def _base_entries(root: Path, commit: str, paths: Sequence[str]) -> dict[str, _BaseEntry]:
    result: dict[str, _BaseEntry] = {}
    for path in paths:
        data = _git_bytes(
            root,
            "--literal-pathspecs",
            "ls-tree",
            "-z",
            "--full-tree",
            commit,
            "--",
            path,
        )
        entry = _parse_ls_tree(data).get(_path_bytes(path))
        if entry is not None:
            result[path] = entry
    return result


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _base_content_hash(root: Path, entry: _BaseEntry) -> str | None:
    if entry.object_type != "blob":
        return None
    data = _git_bytes(root, "cat-file", "blob", entry.object_id)
    return _hash_bytes(data)


def _validate_base_entry(entry: _BaseEntry) -> None:
    if entry.object_type not in {"blob", "tree", "commit"}:
        raise SnapshotError(f"unsupported base tree entry type: {entry.object_type}")
    if entry.object_type == "blob" and entry.mode not in {"100644", "100755", "120000"}:
        raise SnapshotError(f"unsupported base file mode: {entry.mode}")
    if entry.object_type == "tree" and entry.mode != "040000":
        raise SnapshotError(f"unsupported base tree mode: {entry.mode}")
    if entry.object_type == "commit" and entry.mode != "160000":
        raise SnapshotError(f"unsupported base gitlink mode: {entry.mode}")


def _hash_worktree_entry(path: Path) -> tuple[str, str, str]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise SnapshotError(f"cannot inspect worktree path {path}: {exc}") from exc
    mode_bits = metadata.st_mode
    if stat.S_ISLNK(mode_bits):
        try:
            content = os.fsencode(os.readlink(path))
        except OSError as exc:
            raise SnapshotError(f"cannot read worktree symlink {path}: {exc}") from exc
        return "present", "120000", _hash_bytes(content)
    if not stat.S_ISREG(mode_bits):
        raise SnapshotError(f"allowlisted path is not a regular file or symlink: {path}")
    mode = "100755" if mode_bits & 0o111 else "100644"
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SnapshotError(f"cannot read worktree path {path}: {exc}") from exc
    return "present", mode, digest.hexdigest()


def _safe_worktree_path(root: Path, path: str) -> Path:
    candidate = root.joinpath(*path.split("/"))
    current = root
    components = path.split("/")
    for component in components[:-1]:
        current /= component
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            raise SnapshotError(f"cannot inspect worktree path {current}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise SnapshotError(f"allowlisted path contains a symlinked parent: {path}")
    return candidate


def _parse_index(data: bytes) -> dict[bytes, tuple[str, str, int]]:
    entries: dict[bytes, tuple[str, str, int]] = {}
    for record in data.split(b"\0"):
        if not record:
            continue
        try:
            header, path = record.split(b"\t", 1)
            mode, object_id, stage = header.split()
            parsed = (mode.decode("ascii"), object_id.decode("ascii"), int(stage))
        except (ValueError, UnicodeDecodeError) as exc:
            raise SnapshotError("Git returned an invalid index entry") from exc
        if path in entries:
            raise SnapshotError(f"index contains duplicate entries for {os.fsdecode(path)!r}")
        entries[path] = parsed
    return entries


def _index_entries(root: Path, paths: Sequence[str]) -> dict[str, tuple[str, str]]:
    if not paths:
        return {}
    data = _git_bytes(root, "--literal-pathspecs", "ls-files", "--stage", "-z", "--", *paths)
    parsed = _parse_index(data)
    result: dict[str, tuple[str, str]] = {}
    for path in paths:
        values = parsed.get(_path_bytes(path))
        if values is None:
            continue
        mode, object_id, stage = values
        if stage != 0:
            raise SnapshotError(f"allowlisted path has an unmerged index entry: {path}")
        if mode not in {"100644", "100755", "120000"}:
            raise SnapshotError(f"unsupported index file mode for {path}: {mode}")
        result[path] = (mode, object_id)
    return result


def _index_content_hash(root: Path, object_id: str) -> str:
    return _hash_bytes(_git_bytes(root, "cat-file", "blob", object_id))


def _parse_status(data: bytes) -> tuple[set[bytes], set[bytes]]:
    staged: set[bytes] = set()
    dirty: set[bytes] = set()
    for record in data.split(b"\0"):
        if not record:
            continue
        if len(record) < 3 or record[2:3] != b" ":
            raise SnapshotError("Git returned an invalid status entry")
        index_status, worktree_status = record[0:1], record[1:2]
        path = record[3:]
        if index_status not in {b" ", b"?"}:
            staged.add(path)
        if worktree_status not in {b" "} or index_status == b"?":
            dirty.add(path)
    return staged, dirty


def _preflight(
    root: Path,
    allowlist: Sequence[str],
    *,
    exclude_paths: Iterable[str] = (),
) -> dict[str, Any]:
    status = _git_bytes(
        root,
        "status",
        "--porcelain=v1",
        "--no-renames",
        "--untracked-files=all",
        "-z",
        "--",
    )
    staged_raw, dirty_raw = _parse_status(status)
    allowed = {_path_bytes(path) for path in allowlist}
    excluded = {_path_bytes(path) for path in exclude_paths}

    def external(raw_paths: Iterable[bytes]) -> list[str]:
        paths = {path for path in raw_paths if path not in allowed and path not in excluded}
        return sorted(os.fsdecode(path).rstrip("/") for path in paths)

    external_staged = external(staged_raw)
    external_dirty = external(dirty_raw)
    return {
        "external_dirty_paths": external_dirty,
        "external_staged_paths": external_staged,
        "shipping_blocked": bool(external_dirty or external_staged),
    }


def snapshot(
    repo: Path | str,
    base_commit: str,
    allowlist: Sequence[str] | Mapping[str, Any] | str,
    source: str = "worktree",
    *,
    exclude_paths: Iterable[str] = (),
) -> SnapshotResult:
    """Build a snapshot without changing the repository or its index."""

    if source not in {"worktree", "index"}:
        raise SnapshotError("source must be worktree or index")
    root = repository_root(repo)
    commit = _resolve_base_commit(root, base_commit)
    if isinstance(allowlist, (dict, str)):
        paths = normalize_allowlist(allowlist)
    else:
        paths = normalize_allowlist({"version": 1, "paths": list(allowlist)})
    base = _base_entries(root, commit, paths)
    for entry in base.values():
        _validate_base_entry(entry)

    manifest_paths: list[dict[str, Any]] = []
    if source == "index":
        indexed = _index_entries(root, paths)
        for path in paths:
            entry = base.get(path)
            selected = indexed.get(path)
            if selected is None:
                if entry is None:
                    state, mode, content = "absent", None, None
                else:
                    state, mode = "deleted", entry.mode
                    content = _base_content_hash(root, entry)
            else:
                mode, object_id = selected
                state, content = "present", _index_content_hash(root, object_id)
            manifest_paths.append(
                {"content_sha256": content, "mode": mode, "path": path, "state": state}
            )
    else:
        for path in paths:
            entry = base.get(path)
            worktree_path = _safe_worktree_path(root, path)
            try:
                state, mode, content = _hash_worktree_entry(worktree_path)
            except FileNotFoundError:
                if entry is None:
                    state, mode, content = "absent", None, None
                else:
                    state, mode = "deleted", entry.mode
                    content = _base_content_hash(root, entry)
            manifest_paths.append(
                {"content_sha256": content, "mode": mode, "path": path, "state": state}
            )

    manifest: dict[str, Any] = {"base_commit": commit, "paths": manifest_paths}
    canonical = json.dumps(
        manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False
    ).encode("utf-8")
    identity = "sha256:" + hashlib.sha256(canonical).hexdigest()
    preflight = _preflight(root, paths, exclude_paths=exclude_paths)
    if source == "index" and preflight["external_staged_paths"]:
        joined = ", ".join(preflight["external_staged_paths"])
        raise SnapshotError(f"external staged paths are not allowed in index mode: {joined}")
    return SnapshotResult(manifest, identity, preflight)


def _atomic_write(path: Path, payload: bytes) -> None:
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SnapshotError(f"cannot create manifest directory: {exc}") from exc
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise SnapshotError(f"cannot atomically write manifest: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--allowlist-json", required=True)
    parser.add_argument("--source", required=True, choices=("worktree", "index"))
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        output = args.output.expanduser()
        root = repository_root(args.repo)
        exclude: tuple[str, ...] = ()
        try:
            relative = output.resolve(strict=False).relative_to(root)
        except ValueError:
            pass
        else:
            exclude = (relative.as_posix(),)
        result = snapshot(
            root,
            args.base_commit,
            args.allowlist_json,
            args.source,
            exclude_paths=exclude,
        )
        payload = (
            json.dumps(result.manifest, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            + "\n"
        ).encode("utf-8")
        _atomic_write(output, payload)
        print(
            json.dumps(
                {"preflight": result.preflight, "review_snapshot_id": result.review_snapshot_id},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except (SnapshotError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
