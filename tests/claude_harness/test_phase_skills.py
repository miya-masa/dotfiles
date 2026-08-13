"""Claude Code 側 software delivery workflow の記述契約テスト (spec A1-A12)."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "dot_claude/skills"
PHASES = (
    "product-discovery",
    "implementation-planning",
    "execute-plan",
    "ship-change",
    "execute-and-ship",
    "post-merge-cleanup",
)


def read_skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def read_reference(skill: str, name: str) -> str:
    return (SKILLS / skill / "references" / name).read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields


def test_a1_phase_skills_exist_with_triggers_and_exclusions() -> None:
    assert {path.name for path in SKILLS.iterdir() if path.is_dir()} >= set(PHASES)

    for name in PHASES:
        text = read_skill(name)
        fields = frontmatter(text)

        assert fields["name"] == name
        description = fields["description"]
        assert "起動" in description or "使う" in description
        assert "使わない" in description
        assert len(text.splitlines()) <= 65


def test_a2_discovery_stops_before_planning_without_approval() -> None:
    body = read_skill("product-discovery")
    reference = read_reference("product-discovery", "spec-and-plan.md")

    assert "明示承認するまで" in body
    assert "進まない" in body
    assert "implementation-planning" in body
    assert "明示承認するまで planning へ handoff しない" in reference


def test_a3_planning_offers_execution_choice_and_stops() -> None:
    body = read_skill("implementation-planning")

    assert "execute-plan" in body
    assert "execute-and-ship" in body
    assert "二択" in body
    assert "実装を開始せず" in body
    assert "shipping 権限だけ" in body


def test_a4_execute_plan_stops_at_local_complete() -> None:
    body = read_skill("execute-plan")
    reference = read_reference("execute-plan", "task-execution.md")

    assert "LOCAL_COMPLETE" in body
    assert "commit しない" in body
    for forbidden in ("push", "MR", "merge", "release", "tag"):
        assert forbidden in body
    assert "ship-change" in body
    assert "commit しない" in reference


def test_a5_ship_change_stops_before_merge() -> None:
    body = read_skill("ship-change")
    reference = read_reference("ship-change", "shipping.md")

    assert "merge しない" in body
    assert "release" in body
    assert "tag" in body
    assert "ready な MR" in body
    assert "終端" in body
    assert "post-merge-cleanup" in body
    assert "ready な MR" in reference


def test_a6_cleanup_requires_explicit_request_merge_and_git_confirmation() -> None:
    body = read_skill("post-merge-cleanup")
    reference = read_reference("post-merge-cleanup", "cleanup.md")

    assert "明示依頼" in body
    assert "merge 済み" in body
    assert "付けない" in body
    for flag in ("--force", "--no-hooks", "--yes"):
        assert flag in body
        assert flag in reference
    for check in ("git worktree list", "git branch --list"):
        assert check in body
        assert check in reference
    assert "artifact は削除しない" in body
    assert "`ARTIFACT_REMOVE` へは進めない" in body
    assert "cleanup_result.py" not in body
    assert "cleanup_result.py" not in reference


def test_a7_every_phase_states_its_non_authority() -> None:
    for name in PHASES:
        body = read_skill(name)
        assert "この phase が行わないこと" in body

    assert "shipping 権限は" in read_skill("execute-plan")
    assert "shipping を認可しない" in read_skill("ship-change")
    assert "認可しない" in read_skill("execute-and-ship")


def test_a8_task_execution_requires_red_reason_then_minimal_green() -> None:
    body = read_skill("execute-plan")
    reference = read_reference("execute-plan", "task-execution.md")

    for text in (body, reference):
        assert "RED 理由" in text
        assert "最小の GREEN" in text
    assert "RED → 期待した RED 理由の確認 → 最小の GREEN" in reference
    assert "実行時に TDD 例外を発明しない" in reference


def test_a9_plan_tasks_declare_nine_fields() -> None:
    reference = read_reference("product-discovery", "spec-and-plan.md")
    planning = read_skill("implementation-planning")

    for field in (
        "goal",
        "owned paths",
        "deliverables",
        "dependencies",
        "interfaces",
        "acceptance criteria",
        "validation",
        "RED 理由",
        "stop conditions",
    ):
        assert field in reference
        assert field in planning
    assert "decision-complete" in reference


def test_a10_short_path_requires_artifact_and_choice_without_preflight() -> None:
    reference = read_reference("product-discovery", "spec-and-plan.md")
    body = read_skill("product-discovery")

    for text in (reference, body):
        assert "01-short-path.md" in text
        assert "task-reviewer" not in text
        assert (
            "preflight review は挟まない" in text
            or "preflight review も挟まない" in text
        )
        assert "二択" in text
    assert "ファイル数" in reference and "ファイル数" in body
    assert "acceptance criteria" in reference
    assert "validation command" in reference
    assert "実行方法のユーザー選択を省略しない" in reference
    assert "実行方法のユーザー選択を省略しない" in body


def test_a11_snapshot_equality_gate_brackets_staging_and_commit() -> None:
    body = read_skill("ship-change")
    reference = read_reference("ship-change", "shipping.md")

    for text in (body, reference):
        assert "staging の直前" in text
        assert "commit の直前" in text
        assert "review と verification" in text
        assert "無効化" in text
    assert "厳密に一致" in body
    assert "厳密に等しい" in reference


def test_a12_resume_starts_at_first_incomplete_gate() -> None:
    execute = read_skill("execute-plan")
    execute_reference = read_reference("execute-plan", "task-execution.md")
    ship = read_skill("ship-change")
    ship_reference = read_reference("ship-change", "shipping.md")

    for text in (execute, execute_reference):
        assert "最初の未完了 gate" in text
        assert "再 dispatch" in text
    for text in (ship, ship_reference):
        assert "resume" in text
        assert "再利用" in text
        assert "重複させない" in text
    assert "外部 write を重複させない" in execute


def test_spec_review_keeps_the_claude_design_lenses() -> None:
    """spec §1.3: Codex 型 (Completeness/Simplicity) へ縮めず Claude 側レンズを維持する。"""
    body = read_skill("product-discovery")
    reference = read_reference("product-discovery", "spec-and-plan.md")
    lenses = (
        ROOT / "dot_agents/workflows/software_delivery/references/review-lenses.md"
    ).read_text(encoding="utf-8")

    for text in (body, reference):
        for lens in ("Completeness", "Soundness", "Operability", "Simplicity"):
            assert lens in text
        assert "Adversarial" in text
    for lens in ("Soundness", "Operability"):
        assert lens in lenses


def test_documented_state_graph_matches_the_helper() -> None:
    """自前で書いた CLI 契約が helper の PHASES/TRANSITIONS と乖離していないこと。"""
    import importlib.util

    script = ROOT / "dot_agents/workflows/software_delivery/scripts/workflow_state.py"
    spec = importlib.util.spec_from_file_location("workflow_state_doc", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    doc = read_reference("execute-plan", "state-and-artifacts.md")
    for phase in module.PHASES:
        assert phase in doc, f"未記載の phase: {phase}"
    for bogus in ("EXECUTE", "SHIP"):
        assert bogus not in module.PHASES
        assert not re.search(rf"(?<![A-Z_]){bogus}(?![A-Z_])", doc), (
            f"存在しない phase: {bogus}"
        )
    assert "STOPPED" not in module.PHASES
    assert "`STOPPED` phase は存在しない" in doc

    # 主要な前進辺が実グラフに存在すること (doc の chain が机上の産物でないこと)。
    for source, target in (
        ("DISCOVERY", "SPEC_DRAFT"),
        ("SPEC_REVIEWS", "USER_APPROVED_SPEC"),
        ("PLAN_REVIEW", "EXECUTION_CHOICE"),
        ("EXECUTION_CHOICE", "WORKTREE_READY"),
        ("LOCAL_VERIFICATION", "LOCAL_COMPLETE"),
        ("LOCAL_COMPLETE", "COMMIT"),
        ("MR_READY", "MERGE_CHECK"),
        ("WT_REMOVE", "ARTIFACT_REMOVE"),
    ):
        assert target in module.TRANSITIONS[source]


def test_shipping_authorization_records_a_concrete_command() -> None:
    doc = read_reference("execute-plan", "state-and-artifacts.md")

    assert "shipping_authorized" in doc
    assert "--patch-json" in doc
    assert "execute-and-ship" in doc
