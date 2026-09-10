"""Semantic contracts for durable checkpoints and D/AC traceability."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC_AGENT = ROOT / "dot_codex/agents/specification.toml"
PLANNING_AGENT = ROOT / "dot_codex/agents/planning.toml"
PLANNING = ROOT / "dot_codex/skills/implementation-planning/SKILL.md"
EXECUTE = ROOT / "dot_codex/skills/execute-plan/SKILL.md"
SPEC = ROOT / "dot_codex/workflows/software_delivery/references/spec-and-plan.md"
RECOVERY = ROOT / "dot_codex/workflows/software_delivery/references/state-recovery.md"
EXECUTION = ROOT / "dot_codex/workflows/software_delivery/references/task-execution.md"
LIFECYCLE = (
    ROOT / "dot_codex/workflows/software_delivery/references/artifact-lifecycle.md"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(body: str, heading: str, next_heading: str) -> str:
    start = body.index(heading)
    end = body.index(next_heading, start + len(heading))
    return body[start:end]


def compact(body: str) -> str:
    return " ".join(body.split())


def test_decision_and_acceptance_ids_are_monotonic_and_tombstoned() -> None:
    specification = compact(
        section(read(SPEC), "## 安定したdecisionとacceptanceの追跡性", "### 仕様review")
    )
    agent = compact(read(SPEC_AGENT))

    for phrase in (
        "D<n>",
        "AC<n>",
        "単調に",
        "安定",
        "reason",
        "renumberまたはreuseしません",
        "RETIRED",
        "tombstone",
        "retired",
        "満足証拠なし",
    ):
        assert phrase.lower() in specification.lower(), phrase
    assert specification.index("単調に") < specification.index(
        "renumberまたはreuseしません"
    )
    assert specification.index("renumberまたはreuseしません") < specification.index(
        "RETIRED"
    )
    assert "D<n>" in agent and "AC<n>" in agent
    assert "reason" in agent.lower()
    assert "active ACはplan/task/test/evidenceへリンク" in agent
    assert "retired AC/`RETIRED` identifiersには満足証拠を付けない" in agent
    assert "active ACに満足証拠を付けない" not in agent


def test_plan_tasks_tests_and_evidence_preserve_acceptance_ids() -> None:
    planning = compact(section(read(SPEC), "## acceptanceの追跡性", "## 短縮経路"))
    task_plan = compact(
        section(read(EXECUTION), "## task routingと実装", "## reviewと修正ループ")
    )
    skill = compact(read(PLANNING))
    agent = compact(read(PLANNING_AGENT))
    execute = compact(read(EXECUTE))

    for phrase in (
        "AC ID",
        "exact test target/node ID",
        "command",
        "evidence path",
        "plan",
        "task",
        "tests",
        "evidence",
        "repository test名を変更しない",
    ):
        assert phrase.lower() in planning.lower(), phrase
    assert planning.index("AC ID") < planning.index("exact test target/node ID")
    assert planning.index("exact test target/node ID") < planning.index("command")
    assert planning.index("command") < planning.index("evidence path")
    for phrase in ("acceptance criteria", "evidence", "validation command"):
        assert phrase.lower() in task_plan.lower(), phrase
    for artifact in (planning, task_plan, skill, agent, execute):
        assert "D<n>" in artifact and "AC<n>" in artifact
    for artifact in (agent, skill, execute, task_plan):
        assert "exact test target/node ID" in artifact
        assert "command" in artifact
        assert "evidence path" in artifact
    assert "AC ID" in skill or "AC<n>" in skill
    assert "AC<n>" in agent and "test" in agent.lower() and "evidence" in agent.lower()


def test_gate_commit_and_checkpoint_order_preserves_context_authority() -> None:
    recovery = compact(
        section(read(RECOVERY), "## gateの証拠とbounded checkpoint", "## CLI契約")
    )

    for phrase in (
        "まず証拠を書いて検証",
        "CAS commit",
        "追記",
        "progress.md",
        "context.json",
        "controllerだけ",
        "state authority",
        "checkpoint",
        "追記に失敗",
        "rollbackせず",
        "再構成",
        "ahead-of-state",
        "gateを進めてはならず",
    ):
        assert phrase.lower() in recovery.lower(), phrase
    for field in (
        "workflow ID",
        "phaseとrevision",
        "完了したgate",
        "承認済み`D<n>`の値",
        "関連する`AC<n>` status",
        "未決のdecisionまたはblocker",
        "次のgate",
        "artifact/evidence path",
    ):
        assert field in recovery, field
    positions = [
        recovery.index("まず証拠を書いて検証"),
        recovery.index("CAS commit"),
        recovery.index("追記"),
    ]
    assert positions == sorted(positions)
    assert recovery.index("context.json") < recovery.index("progress.md")
    assert recovery.index(
        "`context.json`とcommit済みartifact evidence"
    ) < recovery.index("欠落したcheckpointを再構成")
    assert recovery.index("ahead-of-state evidence") < recovery.index(
        "gateを進めてはならず"
    )


def test_native_compaction_has_no_manual_handoff_gate_and_resume_is_artifact_driven() -> (
    None
):
    recovery = compact(
        section(
            read(RECOVERY),
            "## native compactionとartifact駆動resume",
            "## gateの証拠とbounded checkpoint",
        )
    )
    execution = compact(
        section(
            read(EXECUTION),
            "## native compactionとartifact駆動resume",
            "## 最終acceptance-criteria review",
        )
    )

    for body in (recovery, execution):
        assert "260,000" in body
        assert "native auto compact" in body.lower()
        assert "手動`/compact`" in body.lower()
        assert "handoff" in body.lower()
        assert "新しいsession" in body.lower()
        assert "要求してはいけません" in body.lower()
        assert "artifact" in body.lower()
        assert "context.json" in body
        assert "commit済み証拠" in body.lower()
        assert "resume" in body.lower()
    assert recovery.index("260,000") < recovery.index("要求してはいけません")
    assert "workflow phaseの変更" in recovery.lower()


def test_final_review_table_exactly_gates_active_acceptance_criteria() -> None:
    review = compact(
        section(
            read(EXECUTION),
            "## 最終acceptance-criteria review",
            "## 最終review、snapshot、ローカル検証",
        )
    )
    specification = compact(section(read(SPEC), "## acceptanceの追跡性", "## 短縮経路"))

    for phrase in (
        "active AC set",
        "AC ID | test/evidence | status",
        "SATISFIED",
        "UNSATISFIED",
        "UNVERIFIED",
        "正確に",
        "Retired",
        "別table",
        "満足証拠を付けません",
        "承認できず",
    ):
        assert phrase.lower() in review.lower(), phrase
    allowed_statuses = set(re.findall(r"`(SATISFIED|UNSATISFIED|UNVERIFIED)`", review))
    assert allowed_statuses == {"SATISFIED", "UNSATISFIED", "UNVERIFIED"}
    assert review.index("active AC set") < review.index(
        "AC ID | test/evidence | status"
    )
    assert review.index("AC ID | test/evidence | status") < review.index("SATISFIED")
    assert review.index("SATISFIED") < review.index("UNSATISFIED")
    assert review.index("UNSATISFIED") < review.index("UNVERIFIED")
    assert review.index("UNVERIFIED") < review.index("承認できず")
    assert review.index("active AC set") < review.index("Retired ID")
    assert review.index("AC ID | test/evidence | status") < review.index("Retired ID")
    assert review.index("Retired ID") < review.index("満足証拠を付けません")
    active = "active `AC<n>` set"
    retired = "retired identifierは別tableに"
    assert active in specification and retired in specification
    assert specification.index(active) < specification.index(retired)


def test_artifact_lint_failure_is_documented_in_recovery_and_execution() -> None:
    recovery = read(RECOVERY)
    execution = read(EXECUTION)

    assert "artifact lint failed" in recovery
    assert "artifact lint failed" in execution
    for phrase in ("Failure", "未検証"):
        assert phrase in execution


def test_final_review_artifact_is_the_lint_target_of_record() -> None:
    lifecycle = compact(read(LIFECYCLE))
    assert "reviews/final-review.md" in lifecycle


def test_short_path_documents_l1_exemption_and_l2_ac_id_source() -> None:
    short_path = compact(
        section(read(SPEC), "## 短縮経路", "## artifactと引き継ぎの不変条件")
    )
    assert "tasks/01-short-path.md" in short_path
    assert "AC" in short_path
    assert "L1" in short_path
    assert "免除" in short_path
    assert "出所" in short_path
