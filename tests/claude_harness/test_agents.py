"""Claude Code subagent 定義の契約テスト (spec A13 と §3.1 の参照更新)."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "dot_claude/agents"


def read_agent(name: str) -> str:
    return (AGENTS / f"{name}.md").read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields


def test_task_reviewer_is_retired_on_the_claude_side() -> None:
    """task 単位の review subagent は Claude では持たない (over-verification 対策)."""
    assert not (AGENTS / "task-reviewer.md").exists()


def test_reviewer_keeps_xhigh_for_the_two_remaining_gates() -> None:
    """残る gate は spec review と final review だけなので effort を下げない."""
    fields = frontmatter(read_agent("reviewer"))

    assert fields["model"] == "opus"
    assert fields["effort"] == "xhigh"
    for forbidden in ("Edit", "Write"):
        assert forbidden not in fields["tools"]


def test_reviewer_points_at_the_shared_review_core() -> None:
    text = read_agent("reviewer")

    assert "workflows/software_delivery/references/analysis-techniques.md" in text
    assert "review-lenses.md" in text
    assert "review-common.md" in text
    assert "skills/spec-review" not in text
    assert "impl-review" not in text


def test_implementer_and_verifier_follow_execute_plan_contracts() -> None:
    implementer = read_agent("implementer")
    verifier = read_agent("verifier")
    explorer = read_agent("explorer")

    assert "execute-plan" in implementer
    assert "RED" in implementer
    assert "test-driven-development" not in implementer

    assert "local verification" in verifier
    assert "verification-before-completion" not in verifier

    assert "systematic-debugging" not in explorer
    assert "bugfix" in explorer
