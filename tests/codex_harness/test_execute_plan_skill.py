"""Task 7 contract tests for the execute-plan phase skill."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "dot_codex/skills/execute-plan"
BODY = SKILL / "SKILL.md"
METADATA = SKILL / "agents/openai.yaml"
REFERENCE = ROOT / "dot_codex/workflows/software_delivery/references/task-execution.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_metadata_is_explicit_and_exact() -> None:
    content = read(METADATA)
    for expected in (
        'display_name: "Execute Plan"',
        'short_description: "TDDとtask reviewで計画をlocal verificationまで実行する"',
        'default_prompt: "Use $execute-plan to implement this reviewed plan with TDD and stop after local verification."',
        "policy:\n  allow_implicit_invocation: false",
    ):
        assert expected in content


def test_skill_is_concise_and_routes_the_execution_boundaries() -> None:
    body = read(BODY)
    assert len(body.splitlines()) <= 65
    assert "TODO" not in body
    for phrase in (
        "reviewed plan",
        "short-path task",
        "context.json",
        "wt switch --create <branch> --base <default> --no-cd --format=json",
        "absolute workdir",
        "fresh Luna Max",
        "serial",
        "RED",
        "minimal GREEN",
        "limited refactor",
        "TDD exception",
        "task-reviewer",
        "Spec compliance",
        "Simplicity",
        "fresh Sol",
        "snapshot",
        "LOCAL_COMPLETE",
        "no commit",
        "ship-change",
        "review-policy.md",
    ):
        assert phrase in body or phrase in read(REFERENCE), phrase


def test_reference_covers_tdd_reviews_resume_and_evidence_gates() -> None:
    reference = read(REFERENCE)
    for phrase in (
        "Entry and resume",
        "artifact",
        "Git evidence",
        "first incomplete gate",
        "completed task",
        "not redispatch",
        "incomplete review",
        "incomplete verification",
        "missing",
        "inconsistent",
        "wt switch --create <branch> --base <default> --no-cd --format=json",
        "absolute",
        "one task",
        "RED",
        "RED reason",
        "minimal GREEN",
        "limited refactor",
        "approved TDD exception",
        "Spec compliance",
        "Simplicity",
        "finding",
        "scoped re-review",
        "two failed fixes",
        "debugging",
        "final review",
        "Sol",
        "review snapshot",
        "important task finding required a fix loop",
        "local verification",
        "LOCAL_COMPLETE",
        "commit",
        "ship-change",
        "stop",
    ):
        assert phrase in reference, phrase


def test_reference_preserves_snapshot_binding_and_no_commit_boundary() -> None:
    reference = read(REFERENCE)
    for phrase in (
        "same snapshot",
        "review_snapshot_id",
        "fixed merge-base",
        "final review",
        "local verification",
        "never a commit",
        "shipping authorization",
        "next phase",
    ):
        assert phrase in reference, phrase
