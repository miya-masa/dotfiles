"""Task 6 contract tests for the discovery and planning phase skills."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "dot_codex/skills/product-discovery"
PLANNING = ROOT / "dot_codex/skills/implementation-planning"
REFERENCE = ROOT / "dot_codex/workflows/software_delivery/references/spec-and-plan.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_metadata_is_explicit_and_exact() -> None:
    discovery = read(DISCOVERY / "agents/openai.yaml")
    planning = read(PLANNING / "agents/openai.yaml")
    expected = {
        "product-discovery": (
            'display_name: "Product Discovery"',
            'short_description: "曖昧な機能アイデアを対話とfresh reviewで仕様化する"',
            'default_prompt: "Use $product-discovery to refine this idea into an approved, reviewed specification."',
        ),
        "implementation-planning": (
            'display_name: "Implementation Planning"',
            'short_description: "承認済みspecをreview済みの実行計画へ変換する"',
            'default_prompt: "Use $implementation-planning to turn the approved specification into a reviewed task plan."',
        ),
    }
    for name, values in expected.items():
        content = discovery if name == "product-discovery" else planning
        for value in values:
            assert value in content
        assert "policy:\n  allow_implicit_invocation: false" in content


def test_discovery_has_review_approval_short_path_and_handoff_gates() -> None:
    body = read(DISCOVERY / "SKILL.md")
    reference = read(REFERENCE)
    for phrase in (
        "原則1問",
        "Completeness",
        "Simplicity",
        "Risk",
        "互いの結論を共有しない",
        "採用・却下",
        "明示承認",
        "short path",
        "task-reviewer",
        "implementation-planning",
        "execute-plan",
        "execute-and-ship",
    ):
        assert phrase in body or phrase in reference, phrase
    assert "確認前は" in body
    assert "preflight" in body or "preflight" in reference
    normal_handoff = next(line for line in body.splitlines() if "通常のreview済みspec完了時" in line)
    assert "implementation-planning" in normal_handoff
    assert "execute-plan" not in normal_handoff
    assert "execute-and-ship" not in normal_handoff
    short_path = next(line for line in body.splitlines() if "short pathは" in line)
    assert "task-reviewer" in short_path
    assert "execute-plan" in short_path and "execute-and-ship" in short_path


def test_planning_requires_approved_spec_and_returns_execution_choice() -> None:
    body = read(PLANNING / "SKILL.md")
    reference = read(REFERENCE)
    for phrase in (
        "承認済み",
        "owned paths",
        "成果物",
        "依存",
        "interface",
        "acceptance criteria",
        "検証command",
        "期待するRED理由",
        "stop条件",
        "vertical slice",
        "Sol High",
        "product-discovery",
        "execute-plan",
        "execute-and-ship",
    ):
        assert phrase in body or phrase in reference, phrase
    assert "実装を開始しない" in body or "実装を開始しない" in reference


def test_shared_reference_defines_artifacts_and_review_packets() -> None:
    reference = read(REFERENCE)
    for phrase in (
        "spec.md",
        "plan.md",
        "SHORT_TASK_DRAFT",
        "SHORT_TASK_PREFLIGHT",
        "Completeness",
        "Simplicity",
        "Risk",
        "adopted",
        "rejected",
        "Given/When/Then",
        "normative gap",
    ):
        assert phrase in reference, phrase


def test_skill_bodies_are_concise() -> None:
    for skill in (DISCOVERY, PLANNING):
        assert len(read(skill / "SKILL.md").splitlines()) <= 65
