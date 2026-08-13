#!/usr/bin/env python3
"""Validate and atomically update a software-delivery workflow context.

The context file is the machine-readable state authority for a workflow.  This
module intentionally uses only the Python standard library so it can be called
from a skill without first installing project dependencies.
"""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
import uuid

try:
    import fcntl
except ImportError:  # pragma: no cover - the supported runtime is POSIX.
    fcntl = None  # type: ignore[assignment]


class StateError(Exception):
    """An invalid context or state mutation."""


# STOPPED is deliberately not a phase.  An external blocker is represented by
# USER_DECISION_REQUIRED and state.stopped_from, as specified by the workflow
# state graph.
PHASES = frozenset(
    {
        "DISCOVERY",
        "SPEC_DRAFT",
        "SHORT_TASK_DRAFT",
        "SHORT_TASK_PREFLIGHT",
        "SPEC_REVIEWS",
        "USER_APPROVED_SPEC",
        "PLAN",
        "PLAN_REVIEW",
        "EXECUTION_CHOICE",
        "WORKTREE_READY",
        "TASKS",
        "FINAL_REVIEW",
        "LOCAL_VERIFICATION",
        "LOCAL_COMPLETE",
        "COMMIT",
        "PUSH_MR",
        "CI",
        "MR_READY",
        "MERGE_CHECK",
        "WT_REMOVE",
        "ARTIFACT_REMOVE",
        "DEBUGGING",
        "USER_DECISION_REQUIRED",
    }
)


# Forward transitions, the explicitly specified return transitions, and the
# stop edge available from any non-terminal phase are kept as a small table so
# an invalid jump cannot silently become a product decision.
TRANSITIONS: dict[str, frozenset[str]] = {
    "DISCOVERY": frozenset(
        {"SPEC_DRAFT", "SHORT_TASK_DRAFT", "USER_DECISION_REQUIRED"}
    ),
    "SPEC_DRAFT": frozenset({"SPEC_REVIEWS", "DISCOVERY", "USER_DECISION_REQUIRED"}),
    # EXECUTION_CHOICE is reachable directly because the Claude adapter drops the
    # preflight review subagent; Codex still routes through SHORT_TASK_PREFLIGHT.
    "SHORT_TASK_DRAFT": frozenset(
        {"SHORT_TASK_PREFLIGHT", "EXECUTION_CHOICE", "DISCOVERY", "USER_DECISION_REQUIRED"}
    ),
    "SHORT_TASK_PREFLIGHT": frozenset(
        {"EXECUTION_CHOICE", "SHORT_TASK_DRAFT", "DISCOVERY", "USER_DECISION_REQUIRED"}
    ),
    "SPEC_REVIEWS": frozenset(
        {"USER_APPROVED_SPEC", "DISCOVERY", "USER_DECISION_REQUIRED"}
    ),
    "USER_APPROVED_SPEC": frozenset({"PLAN", "SPEC_REVIEWS", "USER_DECISION_REQUIRED"}),
    "PLAN": frozenset({"PLAN_REVIEW", "DISCOVERY", "USER_DECISION_REQUIRED"}),
    "PLAN_REVIEW": frozenset({"EXECUTION_CHOICE", "PLAN", "USER_DECISION_REQUIRED"}),
    "EXECUTION_CHOICE": frozenset({"WORKTREE_READY", "USER_DECISION_REQUIRED"}),
    "WORKTREE_READY": frozenset({"TASKS", "USER_DECISION_REQUIRED"}),
    "TASKS": frozenset({"FINAL_REVIEW", "DEBUGGING", "USER_DECISION_REQUIRED"}),
    "FINAL_REVIEW": frozenset(
        {"LOCAL_VERIFICATION", "TASKS", "DEBUGGING", "USER_DECISION_REQUIRED"}
    ),
    "LOCAL_VERIFICATION": frozenset(
        {"LOCAL_COMPLETE", "COMMIT", "TASKS", "DEBUGGING", "USER_DECISION_REQUIRED"}
    ),
    "LOCAL_COMPLETE": frozenset({"COMMIT", "USER_DECISION_REQUIRED"}),
    "COMMIT": frozenset({"PUSH_MR", "USER_DECISION_REQUIRED"}),
    "PUSH_MR": frozenset({"CI", "USER_DECISION_REQUIRED"}),
    "CI": frozenset({"MR_READY", "TASKS", "DEBUGGING", "USER_DECISION_REQUIRED"}),
    "MR_READY": frozenset({"MERGE_CHECK", "USER_DECISION_REQUIRED"}),
    "MERGE_CHECK": frozenset({"WT_REMOVE", "USER_DECISION_REQUIRED"}),
    "WT_REMOVE": frozenset({"ARTIFACT_REMOVE", "USER_DECISION_REQUIRED"}),
    "ARTIFACT_REMOVE": frozenset(),
    "DEBUGGING": frozenset({"TASKS", "USER_DECISION_REQUIRED"}),
    # A user-decision stop is resumed explicitly (or invalidated with the
    # normative command), rather than allowing an arbitrary phase jump here.
    "USER_DECISION_REQUIRED": frozenset(),
}


TOP_LEVEL_FIELDS = frozenset(
    {"identity", "workspace", "state", "authorization", "artifacts", "execution", "shipping"}
)
IDENTITY_FIELDS = frozenset(
    {"schema_version", "workflow_id", "source_root", "artifact_root", "default_branch", "base_commit"}
)
WORKSPACE_FIELDS = frozenset({"worktree_path", "branch"})
STATE_FIELDS = frozenset({"phase", "stopped_from", "artifact_revision"})
AUTHORIZATION_FIELDS = frozenset({"shipping_authorized"})
ARTIFACT_FIELDS = frozenset(
    {"spec_path", "plan_path", "tasks_path", "reviews_path", "verification_path"}
)
EXECUTION_FIELDS = frozenset({"tasks", "gates", "choice", "review_snapshot_id"})
SHIPPING_FIELDS = frozenset({"commit", "push", "mr", "ci"})


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise StateError(f"{label} must be an object")
    return value


def _required(mapping: Mapping[str, Any], fields: frozenset[str], label: str) -> None:
    missing = sorted(fields - mapping.keys())
    if missing:
        raise StateError(f"{label} missing required field(s): {', '.join(missing)}")


def _string(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value:
        raise StateError(f"{label} must be a non-empty string")


def _nullable_string(value: Any, label: str) -> None:
    _string(value, label, nullable=True)


def _validate_context_shape(context: Mapping[str, Any]) -> None:
    _required(context, TOP_LEVEL_FIELDS, "context")

    identity = _mapping(context["identity"], "identity")
    _required(identity, IDENTITY_FIELDS, "identity")
    if identity["schema_version"] != 1 or isinstance(identity["schema_version"], bool):
        raise StateError("identity.schema_version must be 1")
    for field in IDENTITY_FIELDS - {"schema_version"}:
        _string(identity[field], f"identity.{field}")

    workspace = _mapping(context["workspace"], "workspace")
    _required(workspace, WORKSPACE_FIELDS, "workspace")
    _nullable_string(workspace["worktree_path"], "workspace.worktree_path")
    _nullable_string(workspace["branch"], "workspace.branch")

    state = _mapping(context["state"], "state")
    _required(state, STATE_FIELDS, "state")
    phase = state["phase"]
    if not isinstance(phase, str) or phase not in PHASES:
        raise StateError(f"state.phase is not a valid phase: {phase!r}")
    stopped_from = state["stopped_from"]
    _nullable_string(stopped_from, "state.stopped_from")
    if stopped_from is not None and stopped_from not in PHASES:
        raise StateError(f"state.stopped_from is not a valid phase: {stopped_from!r}")
    if stopped_from == "USER_DECISION_REQUIRED":
        raise StateError("state.stopped_from cannot be USER_DECISION_REQUIRED")
    if phase != "USER_DECISION_REQUIRED" and stopped_from is not None:
        raise StateError("state.stopped_from is only allowed in USER_DECISION_REQUIRED")
    revision = state["artifact_revision"]
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise StateError("state.artifact_revision must be a non-negative integer")

    authorization = _mapping(context["authorization"], "authorization")
    _required(authorization, AUTHORIZATION_FIELDS, "authorization")
    if not isinstance(authorization["shipping_authorized"], bool):
        raise StateError("authorization.shipping_authorized must be boolean")

    artifacts = _mapping(context["artifacts"], "artifacts")
    _required(artifacts, ARTIFACT_FIELDS, "artifacts")
    _string(artifacts["spec_path"], "artifacts.spec_path")
    _nullable_string(artifacts["plan_path"], "artifacts.plan_path")
    for field in ("tasks_path", "reviews_path", "verification_path"):
        _string(artifacts[field], f"artifacts.{field}")

    execution = _mapping(context["execution"], "execution")
    _required(execution, EXECUTION_FIELDS, "execution")
    if not isinstance(execution["tasks"], dict):
        raise StateError("execution.tasks must be an object")
    if not isinstance(execution["gates"], dict):
        raise StateError("execution.gates must be an object")
    _nullable_string(execution["choice"], "execution.choice")
    _nullable_string(execution["review_snapshot_id"], "execution.review_snapshot_id")

    shipping = _mapping(context["shipping"], "shipping")
    _required(shipping, SHIPPING_FIELDS, "shipping")
    for field in SHIPPING_FIELDS:
        _nullable_string(shipping[field], f"shipping.{field}")


def validate_context(context: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a context and return it as a regular dictionary.

    Unknown fields are retained to permit non-control audit data, while all
    fields required by schema v1 and the state graph are checked.
    """

    if not isinstance(context, dict):
        raise StateError("context must be a JSON object")
    _validate_context_shape(context)
    return context


def load_context(path: Path | str) -> dict[str, Any]:
    context_path = Path(path)
    try:
        raw = context_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StateError(f"cannot read context {context_path}: {exc}") from exc
    try:
        value = json.loads(raw, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise StateError(f"invalid JSON in {context_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError("context JSON must be an object")
    validate_context(value)
    return value


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"invalid JSON constant {value}")


def _deep_merge(target: dict[str, Any], patch: Mapping[str, Any]) -> None:
    for key, value in patch.items():
        if not isinstance(key, str):
            raise StateError("patch keys must be strings")
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def transition_context(
    context: dict[str, Any], to_phase: str, patch: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return context after one validated graph transition.

    ``patch`` is a JSON-object deep merge applied to the candidate state.  The
    command's ``to_phase`` remains authoritative, and the identity/revision
    invariants are enforced by :func:`mutate_context`.
    """

    validate_context(context)
    current = context["state"]["phase"]
    if to_phase not in PHASES:
        raise StateError(f"unknown target phase: {to_phase}")
    if to_phase not in TRANSITIONS[current]:
        raise StateError(f"invalid transition: {current} -> {to_phase}")
    if patch is not None:
        if not isinstance(patch, dict):
            raise StateError("patch-json must contain an object")
        _deep_merge(context, patch)
    context["state"]["phase"] = to_phase
    # A normal transition has no outstanding external-stop origin.  The stop
    # command sets this field explicitly after calling the same mutation path.
    context["state"]["stopped_from"] = None
    return context


def invalidate_normative_context(context: dict[str, Any]) -> dict[str, Any]:
    """Invalidate plan and all downstream gates after a normative change."""

    validate_context(context)
    context["state"]["phase"] = "SPEC_REVIEWS"
    context["state"]["stopped_from"] = None
    context["artifacts"]["plan_path"] = None
    # Task IDs belong to the invalidated plan.  Keep audit history in the
    # append-only progress log (or a separate history field), not as active
    # tasks that a new plan could accidentally treat as completed.
    context["execution"]["tasks"] = {}

    gates = context["execution"]["gates"]
    for name in list(gates):
        gates[name] = "pending" if name == "spec_review" else None
    context["execution"]["choice"] = None
    context["execution"]["review_snapshot_id"] = None
    context["authorization"]["shipping_authorized"] = False
    for name in SHIPPING_FIELDS:
        context["shipping"][name] = None
    return context


def stop_context(context: dict[str, Any], reason: str) -> dict[str, Any]:
    """Represent an external blocker as USER_DECISION_REQUIRED."""

    validate_context(context)
    if not isinstance(reason, str) or not reason.strip():
        raise StateError("stop reason must be a non-empty string")
    current = context["state"]["phase"]
    if current == "USER_DECISION_REQUIRED":
        raise StateError("context is already stopped")
    if current == "ARTIFACT_REMOVE":
        raise StateError("cannot stop terminal ARTIFACT_REMOVE state")
    context["state"]["phase"] = "USER_DECISION_REQUIRED"
    context["state"]["stopped_from"] = current
    return context


def resume_context(context: dict[str, Any]) -> dict[str, Any]:
    """Return an externally stopped context to its recorded prior phase."""

    validate_context(context)
    if context["state"]["phase"] != "USER_DECISION_REQUIRED":
        raise StateError("resume requires USER_DECISION_REQUIRED state")
    previous = context["state"]["stopped_from"]
    if previous is None:
        raise StateError("resume requires state.stopped_from")
    context["state"]["phase"] = previous
    context["state"]["stopped_from"] = None
    return context


def _write_atomic(path: Path, context: Mapping[str, Any]) -> None:
    """Write a complete JSON document and replace ``path`` at the commit point."""

    parent = path.parent
    temporary = parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    payload = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    fd: int | None = None
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise StateError(f"atomic context update failed: {exc}") from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            # The replacement already committed or the original error is more
            # useful than a best-effort cleanup failure.
            pass


@contextmanager
def _context_lock(path: Path):
    """Hold an advisory lock on the containing directory for one CAS update.

    Locking the directory inode, rather than ``context.json``, keeps the lock
    stable across the atomic replacement of that file.  No lock file is
    created or removed, so a stale path cannot be mistaken for ownership.
    """

    if fcntl is None:
        raise StateError("workflow state updates require POSIX directory locking")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path.parent, directory_flags)
    except OSError as exc:
        raise StateError(f"cannot open context directory for locking: {exc}") from exc
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        except OSError as exc:
            raise StateError(f"cannot lock context directory: {exc}") from exc
        try:
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def mutate_context(
    path: Path | str,
    *,
    expected_revision: int,
    operation: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> dict[str, Any]:
    """CAS-update a context, committing only after atomic replacement."""

    context_path = Path(path)
    with _context_lock(context_path):
        current = load_context(context_path)
        if isinstance(expected_revision, bool) or not isinstance(expected_revision, int):
            raise StateError("expected revision must be an integer")
        actual_revision = current["state"]["artifact_revision"]
        if expected_revision != actual_revision:
            raise StateError(
                f"stale artifact revision: expected {expected_revision}, current {actual_revision}"
            )

        candidate = copy.deepcopy(current)
        try:
            result = operation(candidate)
        except StateError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise StateError(f"state operation failed: {exc}") from exc
        if result is None:
            result = candidate
        if not isinstance(result, dict):
            raise StateError("state operation must return a context object")
        if result.get("identity") != current.get("identity"):
            raise StateError("identity fields are immutable")

        # Never trust a patch with a caller-selected revision.  Every
        # successful operation advances exactly one from the CAS value.
        result["state"]["artifact_revision"] = actual_revision + 1
        validate_context(result)
        _write_atomic(context_path, result)
        return result


def _context_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--context", required=True, type=Path)


def _mutation_arguments(parser: argparse.ArgumentParser) -> None:
    _context_argument(parser)
    parser.add_argument("--expected-revision", required=True, type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate context.json")
    _context_argument(validate)

    transition = commands.add_parser("transition", help="apply one state-graph transition")
    _mutation_arguments(transition)
    transition.add_argument("--to", required=True)
    transition.add_argument("--patch-json")

    invalidate = commands.add_parser(
        "invalidate-normative", help="invalidate plan and downstream authorization"
    )
    _mutation_arguments(invalidate)

    stop = commands.add_parser("stop", help="stop for an external blocker")
    _mutation_arguments(stop)
    stop.add_argument("--reason", required=True)

    resume = commands.add_parser("resume", help="resume a stopped context")
    _mutation_arguments(resume)
    return parser


def _patch_argument(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        patch = json.loads(raw, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise StateError(f"invalid --patch-json: {exc}") from exc
    if not isinstance(patch, dict):
        raise StateError("--patch-json must contain an object")
    return patch


def _run(args: argparse.Namespace) -> None:
    if args.command == "validate":
        load_context(args.context)
        return
    if args.command == "transition":
        patch = _patch_argument(args.patch_json)
        mutate_context(
            args.context,
            expected_revision=args.expected_revision,
            operation=lambda context: transition_context(context, args.to, patch),
        )
        return
    if args.command == "invalidate-normative":
        mutate_context(
            args.context,
            expected_revision=args.expected_revision,
            operation=invalidate_normative_context,
        )
        return
    if args.command == "stop":
        mutate_context(
            args.context,
            expected_revision=args.expected_revision,
            operation=lambda context: stop_context(context, args.reason),
        )
        return
    if args.command == "resume":
        mutate_context(
            args.context,
            expected_revision=args.expected_revision,
            operation=resume_context,
        )
        return
    raise StateError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _run(args)
    except (StateError, OSError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
