#!/usr/bin/env python3
"""Create and safely remove project-local software-delivery workflow artifacts.

The helper owns only ``<project>/.aidocs/workflows/<workflow-id>``.  It keeps
that directory outside the target project's tracked tree by using the
repository-local Git exclude when the project does not already ignore
``.aidocs/``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import tempfile
import unicodedata
from typing import Any


WORKFLOW_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\Z")
WORKFLOW_ID_SLUG_LIMIT = 38
IGNORE_RULE = b"/.aidocs/"
TREE_FILES = ("spec.md", "plan.md", "progress.md", "verification.md")


class ArtifactError(Exception):
    """An invalid or unsafe artifact operation."""


def validate_workflow_id(workflow_id: str) -> str:
    if not isinstance(workflow_id, str) or not WORKFLOW_ID_RE.fullmatch(workflow_id):
        raise ArtifactError(
            "workflow-id must match [a-z0-9][a-z0-9-]{0,62} and be one path component"
        )
    return workflow_id


def normalize_slug(value: str | None) -> str:
    """Return the conservative ASCII slug used by :func:`new_workflow_id`."""

    value = value or "workflow"
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return (slug or "workflow")[:WORKFLOW_ID_SLUG_LIMIT].strip("-") or "workflow"


def new_workflow_id(slug: str | None = None) -> str:
    prefix = normalize_slug(slug)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}-{secrets.token_hex(4)}"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ArtifactError(f"Git metadata unavailable: {detail}")
    return result.stdout.strip()


def repository_root(project_root: Path | str | None) -> Path:
    requested = Path(project_root or Path.cwd()).expanduser()
    try:
        requested = requested.resolve(strict=True)
    except OSError as exc:
        raise ArtifactError(f"project root is unavailable: {exc}") from exc
    if not requested.is_dir():
        raise ArtifactError("project root must be a directory")
    try:
        discovered = Path(_git(requested, "rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as exc:
        raise ArtifactError(f"Git repository root is unavailable: {exc}") from exc
    if requested != discovered:
        raise ArtifactError(
            f"project root must be the repository root ({discovered}), got {requested}"
        )
    return discovered


def _path_has_symlink(root: Path, target: Path, *, allow_missing: bool) -> None:
    """Reject symlinks in every path component from root through target."""

    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ArtifactError("artifact path escapes the project root") from exc

    current = root
    try:
        if current.is_symlink():
            raise ArtifactError("project root must not be a symlink")
    except OSError as exc:
        raise ArtifactError(f"cannot inspect project root: {exc}") from exc

    for component in relative.parts:
        current /= component
        try:
            current_lstat = current.lstat()
        except FileNotFoundError:
            if allow_missing:
                return
            raise ArtifactError(f"artifact path does not exist: {current}")
        except OSError as exc:
            raise ArtifactError(f"cannot inspect artifact path {current}: {exc}") from exc
        if stat.S_ISLNK(current_lstat.st_mode):
            raise ArtifactError(f"artifact path contains a symlink: {current}")


def _artifact_paths(root: Path, workflow_id: str, *, allow_missing: bool) -> tuple[Path, Path, Path]:
    validate_workflow_id(workflow_id)
    aidocs = root / ".aidocs"
    workflows = aidocs / "workflows"
    artifact = workflows / workflow_id
    _path_has_symlink(root, artifact, allow_missing=allow_missing)
    return aidocs, workflows, artifact


def _git_exclude_path(root: Path) -> Path:
    raw = _git(root, "rev-parse", "--git-path", "info/exclude")
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    # Inspect the lexical path before resolving it: resolving first would
    # erase evidence that a repository-local metadata component is a symlink.
    try:
        if path.is_relative_to(root):
            _path_has_symlink(root, path, allow_missing=True)
        elif path.exists() and path.is_symlink():
            raise ArtifactError("repository-local Git exclude must not be a symlink")
    except OSError as exc:
        raise ArtifactError(f"cannot inspect Git exclude: {exc}") from exc
    try:
        path = path.resolve(strict=False)
    except OSError as exc:
        raise ArtifactError(f"Git exclude metadata is unavailable: {exc}") from exc
    try:
        path.parent.mkdir(exist_ok=True)
    except OSError as exc:
        raise ArtifactError(f"Git exclude metadata is unavailable: {exc}") from exc
    return path


def _is_ignored(root: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", ".aidocs/"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.strip() or "git check-ignore failed"
    raise ArtifactError(f"cannot verify .aidocs ignore status: {detail}")


def _has_ignore_rule(data: bytes) -> bool:
    return any(line.rstrip(b"\r\n") == IGNORE_RULE for line in data.splitlines())


def ensure_aidocs_ignored(root: Path) -> None:
    if _is_ignored(root):
        return
    exclude = _git_exclude_path(root)
    try:
        data = exclude.read_bytes() if exclude.exists() else b""
    except OSError as exc:
        raise ArtifactError(f"cannot read repository-local Git exclude: {exc}") from exc
    if _has_ignore_rule(data):
        return
    separator = b"" if not data or data.endswith((b"\n", b"\r")) else b"\n"
    try:
        with exclude.open("ab") as handle:
            handle.write(separator + IGNORE_RULE + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ArtifactError(f"cannot update repository-local Git exclude: {exc}") from exc


def _default_branch(root: Path, supplied: str | None) -> str:
    if supplied:
        return supplied
    candidates = (
        ("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"),
        ("branch", "--show-current"),
        ("config", "--get", "init.defaultBranch"),
    )
    for command in candidates:
        result = subprocess.run(
            ["git", *command], cwd=root, text=True, capture_output=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            branch = result.stdout.strip()
            return branch.removeprefix("origin/")
    raise ArtifactError("cannot determine the repository default branch")


def _base_commit(root: Path, supplied: str | None) -> str:
    revision = supplied or "HEAD"
    return _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")


def _state_module() -> Any:
    state_path = Path(__file__).with_name("workflow_state.py")
    if not state_path.is_file() or state_path.is_symlink():
        raise ArtifactError("workflow state validator is unavailable")
    spec = importlib.util.spec_from_file_location("codex_workflow_state", state_path)
    if spec is None or spec.loader is None:
        raise ArtifactError("workflow state validator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initial_context(
    root: Path,
    workflow_id: str,
    artifact: Path,
    default_branch: str,
    base_commit: str,
) -> dict[str, Any]:
    context = {
        "identity": {
            "schema_version": 1,
            "workflow_id": workflow_id,
            "source_root": str(root),
            "artifact_root": str(artifact),
            "default_branch": default_branch,
            "base_commit": base_commit,
        },
        "workspace": {"worktree_path": None, "branch": None},
        "state": {
            "phase": "DISCOVERY",
            "stopped_from": None,
            "artifact_revision": 0,
        },
        "authorization": {"shipping_authorized": False},
        "artifacts": {
            "spec_path": str(artifact / "spec.md"),
            "plan_path": None,
            "tasks_path": str(artifact / "tasks"),
            "reviews_path": str(artifact / "reviews"),
            "verification_path": str(artifact / "verification.md"),
        },
        "execution": {
            "tasks": {},
            "gates": {
                "spec_review": "pending",
                "plan_review": None,
                "final_review": None,
                "local_verification": None,
            },
            "choice": None,
            "review_snapshot_id": None,
        },
        "shipping": {"commit": None, "push": None, "mr": None, "ci": None},
    }
    try:
        _state_module().validate_context(context)
    except Exception as exc:
        raise ArtifactError(f"initial context failed schema validation: {exc}") from exc
    return context


def _write_context(path: Path, context: dict[str, Any]) -> None:
    payload = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8")


def init_artifact(
    project_root: Path | str | None,
    workflow_id: str,
    *,
    default_branch: str | None = None,
    base_commit: str | None = None,
) -> Path:
    validate_workflow_id(workflow_id)
    root = repository_root(project_root)
    _, workflows, artifact = _artifact_paths(root, workflow_id, allow_missing=True)
    if artifact.exists() or artifact.is_symlink():
        raise ArtifactError(f"workflow artifact already exists: {artifact}")
    # Resolve and validate Git metadata before creating any project files.
    branch = _default_branch(root, default_branch)
    commit = _base_commit(root, base_commit)
    ensure_aidocs_ignored(root)
    try:
        workflows.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ArtifactError(f"cannot create artifact parent: {exc}") from exc
    _path_has_symlink(root, workflows, allow_missing=False)
    staging: Path | None = None
    context = initial_context(root, workflow_id, artifact, branch, commit)
    try:
        staging = Path(tempfile.mkdtemp(prefix=f".{workflow_id}.", dir=workflows))
        for filename in TREE_FILES:
            (staging / filename).write_text("", encoding="utf-8")
        (staging / "tasks").mkdir()
        (staging / "reviews").mkdir()
        _write_context(staging / "context.json", context)
        if artifact.exists() or artifact.is_symlink():
            raise ArtifactError(f"workflow artifact already exists: {artifact}")
        os.replace(staging, artifact)
        staging = None
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError(f"cannot initialize workflow artifact: {exc}") from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
    return artifact


def _context_path(artifact: Path, supplied: Path | str | None) -> Path:
    expected = artifact / "context.json"
    if supplied is None:
        return expected
    candidate = Path(supplied).expanduser()
    try:
        if candidate.resolve(strict=False) != expected.resolve(strict=False):
            raise ArtifactError("context path does not match the workflow artifact")
    except OSError as exc:
        raise ArtifactError(f"cannot inspect context path: {exc}") from exc
    return candidate


def remove_artifact(
    project_root: Path | str | None,
    workflow_id: str,
    *,
    expected_revision: int,
    phase: str | None = None,
    authorize: str | None = None,
    context_path: Path | str | None = None,
) -> None:
    validate_workflow_id(workflow_id)
    if phase is not None and phase != "ARTIFACT_REMOVE":
        raise ArtifactError("remove requires phase ARTIFACT_REMOVE")
    if authorize is not None and authorize != "ARTIFACT_REMOVE":
        raise ArtifactError("remove authorization must be ARTIFACT_REMOVE")
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ArtifactError("expected revision must be a non-negative integer")
    root = repository_root(project_root)
    _, _, artifact = _artifact_paths(root, workflow_id, allow_missing=False)
    if artifact.is_symlink() or not artifact.is_dir():
        raise ArtifactError("workflow artifact must be a non-symlink directory")
    context = _context_path(artifact, context_path)
    if context.is_symlink() or not context.is_file():
        raise ArtifactError("workflow context must be a regular file")
    try:
        state = _state_module()
        loaded = state.load_context(context)
    except Exception as exc:
        raise ArtifactError(f"cannot validate workflow context: {exc}") from exc
    identity = loaded["identity"]
    if identity["source_root"] != str(root):
        raise ArtifactError("workflow context source root does not match project root")
    if identity["workflow_id"] != workflow_id:
        raise ArtifactError("workflow context id does not match requested id")
    if identity["artifact_root"] != str(artifact):
        raise ArtifactError("workflow context artifact root does not match requested path")
    state_values = loaded["state"]
    if state_values["phase"] != "ARTIFACT_REMOVE":
        raise ArtifactError("remove requires context phase ARTIFACT_REMOVE")
    if phase is not None and state_values["phase"] != phase:
        raise ArtifactError("requested phase does not match context phase")
    if state_values["artifact_revision"] != expected_revision:
        raise ArtifactError(
            "stale artifact revision: "
            f"expected {expected_revision}, current {state_values['artifact_revision']}"
        )
    try:
        shutil.rmtree(artifact)
    except OSError as exc:
        raise ArtifactError(f"cannot remove workflow artifact: {exc}") from exc


def _workflow_id_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("workflow_id_pos", nargs="?")
    parser.add_argument("--workflow-id", "--id", dest="workflow_id")


def _resolve_workflow_id(args: argparse.Namespace) -> str:
    option = args.workflow_id
    positional = args.workflow_id_pos
    if option and positional and option != positional:
        raise ArtifactError("workflow id was provided twice with different values")
    value = option or positional
    if value is None:
        raise ArtifactError("workflow id is required")
    return validate_workflow_id(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    new_id = commands.add_parser("new-id", help="generate a normalized workflow id")
    new_id.add_argument("slug", nargs="?")
    new_id.add_argument("--project-root", "--root", dest="project_root", type=Path)

    init = commands.add_parser("init", help="initialize a workflow artifact")
    init.add_argument("--project-root", "--root", dest="project_root", type=Path)
    _workflow_id_argument(init)
    init.add_argument("--default-branch")
    init.add_argument("--base-commit")

    remove = commands.add_parser("remove", help="remove one terminal workflow artifact")
    remove.add_argument("--project-root", "--root", dest="project_root", type=Path)
    _workflow_id_argument(remove)
    remove.add_argument("--context", dest="context_path", type=Path)
    remove.add_argument("--expected-revision", "--revision", required=True, type=int)
    remove.add_argument("--phase")
    remove.add_argument("--authorize")
    return parser


def _run(args: argparse.Namespace) -> None:
    if args.command == "new-id":
        value = new_workflow_id(args.slug)
        if args.project_root is not None:
            root = repository_root(args.project_root)
            for _ in range(16):
                _, _, artifact = _artifact_paths(root, value, allow_missing=True)
                if not artifact.exists() and not artifact.is_symlink():
                    break
                value = new_workflow_id(args.slug)
            else:
                raise ArtifactError("could not generate a non-colliding workflow id")
        print(value)
        return
    if args.command == "init":
        workflow_id = _resolve_workflow_id(args)
        print(
            init_artifact(
                args.project_root,
                workflow_id,
                default_branch=args.default_branch,
                base_commit=args.base_commit,
            )
        )
        return
    if args.command == "remove":
        workflow_id = _resolve_workflow_id(args)
        remove_artifact(
            args.project_root,
            workflow_id,
            expected_revision=args.expected_revision,
            phase=args.phase,
            authorize=args.authorize,
            context_path=args.context_path,
        )
        return
    raise ArtifactError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        _run(parser.parse_args(argv))
    except (ArtifactError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
