from __future__ import annotations

import hashlib
import importlib.util
import json
import os
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


def write_artifacts(
    tmp_path: Path,
    *,
    spec_ac: bool = True,
    final_review_satisfied: bool = True,
    verification_complete: bool = True,
) -> None:
    """Write artifact files that satisfy every lint check except opted-out ones.

    Every lint-guarded edge covers more than one artifact, so a test that
    targets one check must still keep the others satisfied or it will fail
    for the wrong (unrecorded) reason.
    """

    spec_text = (
        "- **AC1**: ログイン失敗時にエラーメッセージを表示する\n"
        if spec_ac
        else "no acceptance criteria identifiers here\n"
    )
    (tmp_path / "spec.md").write_text(spec_text, encoding="utf-8")

    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    final_review_text = (
        "| AC1 | tests/foo_test.go::TestBar | SATISFIED |\n"
        if final_review_satisfied
        else "no AC satisfaction table here\n"
    )
    (reviews_dir / "final-review.md").write_text(final_review_text, encoding="utf-8")

    verification_text = (
        "## 失敗履歴\n\n## 未検証範囲\n" if verification_complete else "nothing here\n"
    )
    (tmp_path / "verification.md").write_text(verification_text, encoding="utf-8")


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


def test_spec_without_ac_identifiers_blocks_approval_without_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SPEC_REVIEWS"
    write_context(path, context)
    write_artifacts(tmp_path, spec_ac=False)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "USER_APPROVED_SPEC"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "spec.md" in result.stderr


@pytest.mark.parametrize("marker", ["AC1", "AC-1", "AC_1", "AC 1"])
def test_spec_ac_identifier_variants_allow_approval(
    tmp_path: Path, marker: str
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SPEC_REVIEWS"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "spec.md").write_text(
        f"- **{marker}**: covers the case\n", encoding="utf-8"
    )

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "USER_APPROVED_SPEC"
    )

    assert result.returncode == 0, result.stderr
    updated = read_context(path)
    assert updated["state"]["phase"] == "USER_APPROVED_SPEC"
    assert updated["state"]["artifact_revision"] == 4


def test_spec_ac_identifier_may_repeat_across_lines(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SPEC_REVIEWS"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "spec.md").write_text(
        "- **AC1**: first mention\n- **AC1**: second mention\n", encoding="utf-8"
    )

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "USER_APPROVED_SPEC"
    )

    assert result.returncode == 0, result.stderr
    assert read_context(path)["state"]["artifact_revision"] == 4


def test_spec_path_patch_cannot_bypass_the_lint(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SPEC_REVIEWS"
    write_context(path, context)
    write_artifacts(tmp_path, spec_ac=False)
    elsewhere = tmp_path / "elsewhere-with-ac.md"
    elsewhere.write_text("- **AC1**: covered elsewhere\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(
        path,
        "transition",
        "--expected-revision",
        "3",
        "--to",
        "USER_APPROVED_SPEC",
        "--patch-json",
        json.dumps({"artifacts": {"spec_path": str(elsewhere)}}),
    )

    assert result.returncode != 0
    # 別理由での失敗を lint 迂回の阻止と取り違えないよう、理由まで固定する。
    assert "artifact lint failed" in result.stderr
    assert path.read_bytes() == before


def test_stale_artifact_root_does_not_block_lint_from_the_context_directory(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "SPEC_REVIEWS"
    context["identity"]["artifact_root"] = "/does/not/exist"
    write_context(path, context)
    write_artifacts(tmp_path)

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "USER_APPROVED_SPEC"
    )

    assert result.returncode == 0, result.stderr
    assert read_context(path)["state"]["phase"] == "USER_APPROVED_SPEC"


def test_final_review_missing_file_blocks_local_verification_without_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "reviews" / "final-review.md").unlink()
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "final-review.md" in result.stderr


def test_final_review_without_ac_and_status_on_same_line_blocks_local_verification(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "reviews" / "final-review.md").write_text(
        "AC1 is covered by tests/foo_test.go::TestBar\nresult: SATISFIED\n",
        encoding="utf-8",
    )
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "final-review.md" in result.stderr


def test_final_review_satisfaction_line_is_not_execution_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    before = write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "reviews" / "final-review.md").write_text(
        "| AC1 | tests/foo_test.go::TestBar | SATISFIED |\n", encoding="utf-8"
    )

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode == 1
    assert "E_EVIDENCE" in result.stderr
    assert "artifact lint failed" not in result.stderr
    assert path.read_bytes() == before



def test_final_review_status_words_cannot_authorize_local_verification(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    before = write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "reviews" / "final-review.md").write_text(
        "| AC1 | tests/foo_test.go::TestBar | SATISFIED |\n"
        "| AC2 | tests/bar_test.go::TestBaz | UNSATISFIED |\n"
        "| AC3 | tests/baz_test.go::TestQux | UNVERIFIED |\n",
        encoding="utf-8",
    )

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode == 1
    assert "E_EVIDENCE" in result.stderr
    assert "artifact lint failed" not in result.stderr
    assert path.read_bytes() == before



VERIFICATION_LINT_EDGES = [
    ("LOCAL_VERIFICATION", "LOCAL_COMPLETE"),
    ("LOCAL_VERIFICATION", "COMMIT"),
    ("LOCAL_COMPLETE", "COMMIT"),
]


@pytest.mark.parametrize("from_phase,to_phase", VERIFICATION_LINT_EDGES)
def test_verification_without_failure_heading_blocks_transition_without_mutation(
    tmp_path: Path, from_phase: str, to_phase: str
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = from_phase
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text("## 未検証範囲\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(path, "transition", "--expected-revision", "3", "--to", to_phase)

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "verification.md" in result.stderr


@pytest.mark.parametrize("from_phase,to_phase", VERIFICATION_LINT_EDGES)
def test_verification_without_unverified_heading_blocks_transition_without_mutation(
    tmp_path: Path, from_phase: str, to_phase: str
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = from_phase
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text("## 失敗履歴\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(path, "transition", "--expected-revision", "3", "--to", to_phase)

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "verification.md" in result.stderr


def test_verification_headings_cannot_authorize_local_complete(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    before = write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text(
        "## Failure と修正履歴\n\n## 未実施 / 引き継ぎ\n", encoding="utf-8"
    )

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode == 1
    assert "E_EVIDENCE" in result.stderr
    assert "artifact lint failed" not in result.stderr
    assert path.read_bytes() == before



def test_verification_heading_words_only_in_body_text_still_blocks_transition(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text(
        "失敗はなかった。未検証の範囲もない。\n", encoding="utf-8"
    )
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "verification.md" in result.stderr


# --- AC8: short path skips L1 on every lint edge --------------------------

SHORT_PATH_LINT_EDGES = [
    ("FINAL_REVIEW", "LOCAL_VERIFICATION"),
    ("LOCAL_VERIFICATION", "LOCAL_COMPLETE"),
    ("LOCAL_VERIFICATION", "COMMIT"),
    ("LOCAL_COMPLETE", "COMMIT"),
]


def _write_short_path_marker(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    (tasks_dir / "01-short-path.md").write_text("stub\n", encoding="utf-8")


@pytest.mark.parametrize("from_phase,to_phase", SHORT_PATH_LINT_EDGES)
def test_short_path_lint_exemption_does_not_bypass_evidence_gate(
    tmp_path: Path, from_phase: str, to_phase: str
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = from_phase
    before = write_context(path, context)
    _write_short_path_marker(tmp_path)
    write_artifacts(tmp_path, spec_ac=False)

    result = run_cli(path, "transition", "--expected-revision", "3", "--to", to_phase)

    assert result.returncode == 1
    assert "E_EVIDENCE" in result.stderr
    assert "artifact lint failed" not in result.stderr
    assert path.read_bytes() == before



def test_short_path_still_enforces_l2(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    write_context(path, context)
    _write_short_path_marker(tmp_path)
    write_artifacts(tmp_path, spec_ac=False, final_review_satisfied=False)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "final-review.md" in result.stderr


def test_short_path_still_enforces_l3(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    _write_short_path_marker(tmp_path)
    write_artifacts(tmp_path, spec_ac=False, verification_complete=False)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "verification.md" in result.stderr


# --- AC9: a satisfied spec.md is not treated as short path ----------------


def test_is_short_path_requires_short_path_file_and_unsatisfied_spec_lint(
    tmp_path: Path,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "workflow_state_short_path_helper", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # spec.md も short-path マーカーもなければ通常パス扱い。
    assert module._is_short_path(tmp_path) is False

    _write_short_path_marker(tmp_path)
    (tmp_path / "spec.md").write_text("- **AC1**: has ac\n", encoding="utf-8")
    # spec.md が L1 を満たす限り、marker があっても short path 扱いされない。
    assert module._is_short_path(tmp_path) is False

    (tmp_path / "spec.md").write_text("no ac here\n", encoding="utf-8")
    assert module._is_short_path(tmp_path) is True

    (tmp_path / "spec.md").unlink()
    # spec.md が読めない(不在)場合も L1 不満足と同じ扱いにする。
    assert module._is_short_path(tmp_path) is True


def test_short_path_marker_with_satisfied_spec_still_requires_evidence(
    tmp_path: Path,
) -> None:
    """spec.md が L1 を満たしていれば short-path marker があっても遷移は成功する。

    ``_is_short_path`` は呼び出し時点の spec.md の中身で動的に判定するので、
    L1 が実際に評価されている(かつ満たしている)ことの直接証明は
    ``test_is_short_path_requires_short_path_file_and_unsatisfied_spec_lint`` が
    ``_is_short_path`` を直接呼び出して担う。ここは CLI 経由でその状態が
    壊れていないことの回帰確認。
    """
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    before = write_context(path, context)
    _write_short_path_marker(tmp_path)
    write_artifacts(tmp_path)  # spec_ac=True: spec.md が L1 を満たす。

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode == 1
    assert "E_EVIDENCE" in result.stderr
    assert "artifact lint failed" not in result.stderr
    assert path.read_bytes() == before



# --- AC10: non-linted edges succeed without any artifacts -----------------

NON_LINTED_EDGES = [
    ("PLAN", "PLAN_REVIEW"),
    ("TASKS", "FINAL_REVIEW"),
    ("PLAN_REVIEW", "EXECUTION_CHOICE"),
]


@pytest.mark.parametrize("from_phase,to_phase", NON_LINTED_EDGES)
def test_non_linted_edges_succeed_without_any_artifacts(
    tmp_path: Path, from_phase: str, to_phase: str
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = from_phase
    write_context(path, context)

    result = run_cli(path, "transition", "--expected-revision", "3", "--to", to_phase)

    assert result.returncode == 0, result.stderr
    assert read_context(path)["state"]["phase"] == to_phase


# --- AC11: unreadable artifact I/O fails closed without a traceback -------


def test_non_utf8_verification_file_fails_closed_without_traceback(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_bytes(b"\xff\xfe")
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "Traceback" not in result.stderr


def test_symlink_verification_file_fails_closed_without_traceback(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    target = tmp_path / "verification-target.md"
    target.write_text("## 失敗履歴\n\n## 未検証範囲\n", encoding="utf-8")
    (tmp_path / "verification.md").unlink()
    (tmp_path / "verification.md").symlink_to(target)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "Traceback" not in result.stderr


# --- AC12: multiple missing artifacts are listed in filename order --------


def test_multiple_missing_artifacts_are_listed_in_filename_order_with_examples(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path, spec_ac=False)
    (tmp_path / "verification.md").write_text("nothing here\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    stderr = result.stderr
    assert "artifact lint failed" in stderr

    lines = stderr.splitlines()
    spec_line_idx = next(i for i, line in enumerate(lines) if "spec.md" in line)
    verification_line_idx = next(
        i for i, line in enumerate(lines) if "verification.md" in line
    )
    assert spec_line_idx < verification_line_idx
    assert "期待例:" in lines[spec_line_idx + 1]


# --- check/use race: directory entry is not a regular file ----------------


def test_directory_verification_file_fails_closed_without_traceback(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").unlink()
    (tmp_path / "verification.md").mkdir()
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "Traceback" not in result.stderr


def test_fifo_verification_file_fails_closed_without_hanging(
    tmp_path: Path,
) -> None:
    """A FIFO must fail the lint instead of blocking the open.

    ``O_RDONLY`` on a FIFO waits for a writer, and the open happens while the
    context lock is held, so a blocking open would wedge every concurrent
    mutation as well.
    """

    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").unlink()
    os.mkfifo(tmp_path / "verification.md")
    before = path.read_bytes()

    # run_cli にタイムアウトが無いので、hang を失敗として観測できる形で呼ぶ。
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "transition",
            "--expected-revision",
            "3",
            "--to",
            "LOCAL_COMPLETE",
            "--context",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "Traceback" not in result.stderr


# --- short-path marker must be a regular file, fail-closed otherwise ------


def test_short_path_marker_symlink_does_not_exempt_l1(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    write_context(path, context)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    target = tmp_path / "marker-target.md"
    target.write_text("stub\n", encoding="utf-8")
    (tasks_dir / "01-short-path.md").symlink_to(target)
    write_artifacts(tmp_path, spec_ac=False)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "spec.md" in result.stderr


def test_short_path_marker_directory_does_not_exempt_l1(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "FINAL_REVIEW"
    write_context(path, context)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "01-short-path.md").mkdir()
    write_artifacts(tmp_path, spec_ac=False)
    before = path.read_bytes()

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_VERIFICATION"
    )

    assert result.returncode != 0
    assert path.read_bytes() == before
    assert "artifact lint failed" in result.stderr
    assert "spec.md" in result.stderr


# --- L3 の期待例は不足側に対応する ------------------------------------------


def test_verification_missing_failure_heading_only_gives_failure_example(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text("## 未検証範囲\n", encoding="utf-8")

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    lines = result.stderr.splitlines()
    idx = next(i for i, line in enumerate(lines) if "verification.md" in line)
    assert "期待例: ## 失敗履歴" in lines[idx + 1]
    assert "未検証範囲" not in lines[idx + 1]


def test_verification_missing_unverified_heading_only_gives_unverified_example(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text("## 失敗履歴\n", encoding="utf-8")

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    lines = result.stderr.splitlines()
    idx = next(i for i, line in enumerate(lines) if "verification.md" in line)
    assert "期待例: ## 未検証範囲" in lines[idx + 1]
    assert "失敗履歴" not in lines[idx + 1]


def test_verification_missing_both_headings_gives_combined_example(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.json"
    context = context_fixture()
    context["state"]["phase"] = "LOCAL_VERIFICATION"
    write_context(path, context)
    write_artifacts(tmp_path)
    (tmp_path / "verification.md").write_text("nothing here\n", encoding="utf-8")

    result = run_cli(
        path, "transition", "--expected-revision", "3", "--to", "LOCAL_COMPLETE"
    )

    assert result.returncode != 0
    lines = result.stderr.splitlines()
    idx = next(i for i, line in enumerate(lines) if "verification.md" in line)
    assert "## 失敗履歴" in lines[idx + 1]
    assert "## 未検証範囲" in lines[idx + 1]
