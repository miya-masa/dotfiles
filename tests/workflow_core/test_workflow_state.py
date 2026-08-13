from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "dot_agents/workflows/software_delivery/scripts/workflow_state.py"


def context_fixture() -> dict:
    return {
        "identity": {
            "schema_version": 1,
            "workflow_id": "demo-workflow",
            "source_root": "/repo",
            "artifact_root": "/repo/.aidocs/workflows/demo-workflow",
            "default_branch": "main",
            "base_commit": "a" * 40,
        },
        "workspace": {"worktree_path": "/repo/.worktrees/demo", "branch": "demo"},
        "state": {"phase": "PLAN", "stopped_from": None, "artifact_revision": 3},
        "authorization": {"shipping_authorized": False},
        "artifacts": {
            "spec_path": "/repo/.aidocs/workflows/demo-workflow/spec.md",
            "plan_path": "/repo/.aidocs/workflows/demo-workflow/plan.md",
            "tasks_path": "/repo/.aidocs/workflows/demo-workflow/tasks",
            "reviews_path": "/repo/.aidocs/workflows/demo-workflow/reviews",
            "verification_path": "/repo/.aidocs/workflows/demo-workflow/verification.md",
        },
        "execution": {
            "tasks": {
                "01": {"state": "completed", "history": ["done"]},
                "02": {"state": "pending", "history": []},
            },
            "gates": {
                "spec_review": "passed",
                "plan_review": "passed",
                "final_review": "passed",
                "local_verification": "passed",
            },
            "choice": "execute-and-ship",
            "review_snapshot_id": "sha256:" + "b" * 64,
        },
        "shipping": {
            "commit": "created",
            "push": "created",
            "mr": "open",
            "ci": "passed",
        },
    }


def write_context(path: Path, context: dict | None = None) -> bytes:
    data = json.dumps(context or context_fixture(), indent=2, sort_keys=True) + "\n"
    path.write_text(data, encoding="utf-8")
    return data.encode()


def run_cli(context: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--context", str(context)],
        text=True,
        capture_output=True,
        check=False,
    )


def read_context(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_missing_fields_are_rejected_without_mutation(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    original = write_context(path)
    data = read_context(path)
    del data["identity"]["base_commit"]
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(path, "validate")

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert original != before


def test_invalid_phase_and_transition_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    write_context(path)

    invalid_phase = read_context(path)
    invalid_phase["state"]["phase"] = "NO_SUCH_PHASE"
    path.write_text(json.dumps(invalid_phase), encoding="utf-8")
    result = run_cli(path, "validate")
    assert result.returncode != 0

    write_context(path)
    before = path.read_bytes()
    result = run_cli(path, "transition", "--expected-revision", "3", "--to", "CI")
    assert result.returncode != 0
    assert path.read_bytes() == before


def test_identity_is_immutable(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    write_context(path)
    before = path.read_bytes()

    result = run_cli(
        path,
        "transition",
        "--expected-revision",
        "3",
        "--to",
        "PLAN_REVIEW",
        "--patch-json",
        '{"identity":{"workflow_id":"changed"}}',
    )

    assert result.returncode != 0
    assert path.read_bytes() == before


def test_stale_revision_is_rejected_byte_for_byte(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    write_context(path)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "2", "--to", "PLAN_REVIEW"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before


def test_valid_transition_increments_revision_once(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    write_context(path)

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "PLAN_REVIEW"
    )

    assert result.returncode == 0, result.stderr
    updated = read_context(path)
    assert updated["state"]["phase"] == "PLAN_REVIEW"
    assert updated["state"]["artifact_revision"] == 4


def test_normative_invalidation_clears_active_tasks_and_downstream_state(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    write_context(path)

    result = run_cli(path, "invalidate-normative", "--expected-revision", "3")

    assert result.returncode == 0, result.stderr
    updated = read_context(path)
    assert updated["state"]["phase"] == "SPEC_REVIEWS"
    assert updated["artifacts"]["plan_path"] is None
    assert updated["execution"]["choice"] is None
    assert updated["execution"]["review_snapshot_id"] is None
    assert updated["execution"]["tasks"] == {}
    assert updated["execution"]["gates"]["spec_review"] == "pending"
    assert all(
        value is None
        for name, value in updated["execution"]["gates"].items()
        if name != "spec_review"
    )
    assert updated["authorization"]["shipping_authorized"] is False
    assert updated["shipping"] == {"commit": None, "push": None, "mr": None, "ci": None}


def test_short_path_can_skip_preflight_for_the_claude_adapter(tmp_path: Path) -> None:
    """Claude は preflight review を挟まないので DRAFT から直接 EXECUTION_CHOICE へ行ける."""
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SHORT_TASK_DRAFT"
    write_context(path, context)

    choice = run_cli(
        path,
        "transition",
        "--expected-revision",
        "3",
        "--to",
        "EXECUTION_CHOICE",
    )
    assert choice.returncode == 0, choice.stderr
    assert read_context(path)["state"]["phase"] == "EXECUTION_CHOICE"


def test_short_path_transitions_and_revision_cas(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "DISCOVERY"
    write_context(path, context)

    draft = run_cli(
        path,
        "transition",
        "--expected-revision",
        "3",
        "--to",
        "SHORT_TASK_DRAFT",
    )
    assert draft.returncode == 0, draft.stderr
    assert read_context(path)["state"] == {
        "phase": "SHORT_TASK_DRAFT",
        "stopped_from": None,
        "artifact_revision": 4,
    }

    preflight = run_cli(
        path,
        "transition",
        "--expected-revision",
        "4",
        "--to",
        "SHORT_TASK_PREFLIGHT",
    )
    assert preflight.returncode == 0, preflight.stderr
    assert read_context(path)["state"]["artifact_revision"] == 5

    choice = run_cli(
        path,
        "transition",
        "--expected-revision",
        "5",
        "--to",
        "EXECUTION_CHOICE",
    )
    assert choice.returncode == 0, choice.stderr
    assert read_context(path)["state"] == {
        "phase": "EXECUTION_CHOICE",
        "stopped_from": None,
        "artifact_revision": 6,
    }


def test_short_path_redraft_and_discovery_returns_and_invalid_jump(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SHORT_TASK_PREFLIGHT"
    write_context(path, context)

    redraft = run_cli(
        path,
        "transition",
        "--expected-revision",
        "3",
        "--to",
        "SHORT_TASK_DRAFT",
    )
    assert redraft.returncode == 0, redraft.stderr
    assert read_context(path)["state"]["artifact_revision"] == 4

    context = read_context(path)
    context["state"]["phase"] = "SHORT_TASK_PREFLIGHT"
    context["state"]["artifact_revision"] = 4
    write_context(path, context)
    discovery = run_cli(
        path,
        "transition",
        "--expected-revision",
        "4",
        "--to",
        "DISCOVERY",
    )
    assert discovery.returncode == 0, discovery.stderr
    assert read_context(path)["state"]["artifact_revision"] == 5

    context = read_context(path)
    context["state"]["phase"] = "SHORT_TASK_DRAFT"
    context["state"]["artifact_revision"] = 5
    write_context(path, context)
    before = path.read_bytes()
    invalid = run_cli(
        path,
        "transition",
        "--expected-revision",
        "5",
        "--to",
        "PLAN",
    )
    assert invalid.returncode != 0
    assert path.read_bytes() == before


def test_external_blocker_stop_and_resume_return_to_previous_phase(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    write_context(path)

    stopped = run_cli(
        path,
        "stop",
        "--expected-revision",
        "3",
        "--reason",
        "external blocker",
    )
    assert stopped.returncode == 0, stopped.stderr
    assert read_context(path)["state"] == {
        "phase": "USER_DECISION_REQUIRED",
        "stopped_from": "PLAN",
        "artifact_revision": 4,
    }

    resumed = run_cli(path, "resume", "--expected-revision", "4")
    assert resumed.returncode == 0, resumed.stderr
    assert read_context(path)["state"]["phase"] == "PLAN"
    assert read_context(path)["state"]["stopped_from"] is None
    assert read_context(path)["state"]["artifact_revision"] == 5


def test_terminal_artifact_remove_cannot_be_stopped(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "ARTIFACT_REMOVE"
    write_context(path, context)
    before = path.read_bytes()

    result = run_cli(
        path,
        "stop",
        "--expected-revision",
        "3",
        "--reason",
        "external blocker",
    )

    assert result.returncode != 0
    assert path.read_bytes() == before


def test_debugging_return_is_an_allowed_transition(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    write_context(path)
    data = read_context(path)
    data["state"]["phase"] = "DEBUGGING"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_cli(path, "transition", "--expected-revision", "3", "--to", "TASKS")

    assert result.returncode == 0, result.stderr
    assert read_context(path)["state"]["phase"] == "TASKS"


def test_concurrent_writers_are_serialized_and_one_becomes_stale(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    write_context(path)

    spec = importlib.util.spec_from_file_location("workflow_state_concurrent", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    start = threading.Barrier(2)
    results: list[BaseException | None] = []
    results_lock = threading.Lock()

    def worker() -> None:
        try:
            start.wait(timeout=5)

            def slow_transition(context: dict) -> dict:
                time.sleep(0.15)
                return module.transition_context(context, "PLAN_REVIEW", None)

            module.mutate_context(
                path,
                expected_revision=3,
                operation=slow_transition,
            )
        except BaseException as exc:  # capture both worker outcomes for assertions
            with results_lock:
                results.append(exc)
        else:
            with results_lock:
                results.append(None)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert all(not thread.is_alive() for thread in threads)
    assert len(results) == 2
    assert sum(result is None for result in results) == 1
    errors = [result for result in results if result is not None]
    assert len(errors) == 1
    assert isinstance(errors[0], module.StateError)
    assert "stale artifact revision" in str(errors[0])
    updated = read_context(path)
    assert updated["state"]["artifact_revision"] == 4
    assert updated["state"]["phase"] == "PLAN_REVIEW"


def test_replace_interruption_preserves_old_context_and_removes_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "context.json"
    write_context(path)
    before = path.read_bytes()
    digest = hashlib.sha256(before).hexdigest()

    spec = importlib.util.spec_from_file_location("workflow_state", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def interrupted_replace(source: str | bytes, destination: str | bytes) -> None:
        raise OSError("simulated interruption before replace")

    monkeypatch.setattr(module.os, "replace", interrupted_replace)
    with pytest.raises(module.StateError):
        module.mutate_context(
            path,
            expected_revision=3,
            operation=lambda context: module.transition_context(
                context, "PLAN_REVIEW", None
            ),
        )

    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert list(tmp_path.glob(".context.json.*.tmp")) == []
