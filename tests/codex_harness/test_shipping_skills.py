"""Task 8 contract tests for shipping, cleanup, and the composite phase skills."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill(name: str) -> Path:
    return ROOT / "dot_codex/skills" / name


def test_phase_metadata_is_explicit_and_exact() -> None:
    expected = {
        "ship-change": (
            'display_name: "Ship Change"',
            'short_description: "検証済み変更をcommit・push・MR・CIまで安全に進める"',
            'default_prompt: "Use $ship-change to commit, push, open an MR, and resolve in-scope CI failures."',
        ),
        "post-merge-cleanup": (
            'display_name: "Post-Merge Cleanup"',
            'short_description: "merge済みworkflowのworktreeとartifactを安全に片付ける"',
            'default_prompt: "Use $post-merge-cleanup to verify the merge and safely remove this workflow\'s owned resources."',
        ),
        "execute-and-ship": (
            'display_name: "Execute and Ship"',
            'short_description: "計画を実装しcommit・push・MR・CIまで連続して進める"',
            'default_prompt: "Use $execute-and-ship to execute this reviewed plan and continue through MR-ready CI."',
        ),
    }
    for name, values in expected.items():
        content = read(skill(name) / "agents/openai.yaml")
        for value in values:
            assert value in content
        assert "policy:\n  allow_implicit_invocation: false" in content


def test_skill_bodies_are_concise_and_explicit_only() -> None:
    for name in ("ship-change", "post-merge-cleanup", "execute-and-ship"):
        body = read(skill(name) / "SKILL.md")
        assert len(body.splitlines()) <= 65
        assert "TODO" not in body
        assert "explicit" in body.lower()


def test_ship_change_requires_authorization_and_snapshot_gates() -> None:
    body = read(skill("ship-change") / "SKILL.md")
    for phrase in (
        "shipping authorization",
        "LOCAL_COMPLETE",
        "execute-and-ship handoff",
        "entry or resume",
        "snapshot",
        "commit",
        "remote",
        "MR",
        "CI",
        "allowlist",
        "external dirty",
        "reviewed",
        "verified",
        "staged",
        "controller",
        "logical",
        "fixed default branch",
        "repository status",
        "intended",
        "base/head",
        "secrets",
        "local paths",
        "internal",
        "workflow artifacts",
        "fails closed",
        "suspected contamination",
        "before commit",
        "in-scope",
        "escalation",
        "never merge",
        "no merge",
        "credential",
        "production",
        "release",
        "tag",
    ):
        assert phrase in body, phrase


def test_ship_change_resume_and_stop_contract_is_unambiguous() -> None:
    body = read(skill("ship-change") / "SKILL.md")
    for phrase in (
        "recompute",
        "immediately before staging",
        "preflight",
        "against the index",
        "immediately before commit",
        "no intervening change",
        "exactly equal",
        "mismatch",
        "invalidate",
        "duplicate push",
        "duplicate MR",
        "external blocker",
        "scope expansion",
        "protected contract",
        "permission",
        "runner",
        "stop",
    ):
        assert phrase in body, phrase


def test_cleanup_requires_merge_ownership_exact_command_and_git_confirmation() -> None:
    body = read(skill("post-merge-cleanup") / "SKILL.md")
    reference = read(
        ROOT / "dot_codex/workflows/software_delivery/references/post-merge-cleanup.md"
    )
    for phrase in (
        "explicit",
        "merged",
        "ownership",
        "branch",
        "worktree",
        "artifact",
        "wt remove --foreground --format=json <branch>",
        "--force",
        "-D",
        "--no-hooks",
        "--yes",
        "dirty",
        "unmerged",
        "git worktree list",
        "git branch --list",
        "evidence",
        "WT_REMOVE",
        "ARTIFACT_REMOVE",
        "terminal",
        "no next skill",
    ):
        assert phrase in body or phrase in reference, phrase

    assert "cleanup_result.py" not in body
    assert "branch_outcome" not in body


def test_cleanup_fails_closed_and_keeps_the_artifact() -> None:
    body = read(skill("post-merge-cleanup") / "SKILL.md")
    for phrase in (
        "retained",
        "not_attempted",
        "deferred",
        "invalid JSON",
        "mismatch",
        "keep",
        "hold",
        "does not delete",
        "remote branch deletion is outside this handoff; do not delete it",
        "Do not advance to `ARTIFACT_REMOVE`",
        "`WT_REMOVE` is this phase's terminal state",
    ):
        assert phrase in body, phrase


def test_execute_and_ship_only_composes_execution_and_shipping() -> None:
    body = read(skill("execute-and-ship") / "SKILL.md")
    for phrase in (
        "shipping authorization",
        "execute-plan",
        "ship-change",
        "local verification",
        "MR-ready CI",
        "commit",
        "push",
        "MR",
        "in-scope",
        "does not include",
        "discovery",
        "planning",
        "merge",
        "cleanup",
        "release",
        "tag",
    ):
        assert phrase in body, phrase


def test_shipping_references_existing_state_snapshot_and_cleanup_contracts() -> None:
    ship = read(skill("ship-change") / "SKILL.md")
    cleanup = read(skill("post-merge-cleanup") / "SKILL.md")
    composite = read(skill("execute-and-ship") / "SKILL.md")
    for body in (ship, cleanup, composite):
        assert "context.json" in body
        assert "review-policy.md" in body or "review" in body.lower()
    assert "review_snapshot.py" in ship
    assert "workflow_state.py" in cleanup
    assert "workflow_artifact.py" in cleanup
