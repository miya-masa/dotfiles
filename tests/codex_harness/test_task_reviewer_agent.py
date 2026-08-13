from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "dot_codex/agents/task-reviewer.toml"


def load_agent() -> dict:
    with AGENT.open("rb") as agent_file:
        return tomllib.load(agent_file)


def test_task_reviewer_is_a_luna_max_read_only_reviewer() -> None:
    agent = load_agent()

    assert agent["name"] == "task-reviewer"
    assert "bounded" in agent["description"]
    assert agent["model"] == "gpt-5.6-luna"
    assert agent["model_reasoning_effort"] == "max"
    assert agent["sandbox_mode"] == "read-only"


def test_task_reviewer_contract_keeps_verdicts_and_packet_bounded() -> None:
    instructions = load_agent()["developer_instructions"]
    instruction_lines = instructions.splitlines()

    assert len(instruction_lines) <= 15
    assert "bounded packet" in instructions
    assert "Spec compliance" in instructions
    assert "Simplicity" in instructions
    assert "separate" in instructions
    for field in (
        "goal",
        "acceptance criteria",
        "owned paths",
        "evidence",
        "validation commands",
        "constraints",
        "stop conditions",
    ):
        assert field in instructions


def test_task_reviewer_accepts_short_path_preflight_without_prior_review() -> None:
    instructions = load_agent()["developer_instructions"]

    assert "short-path task draft" in instructions
    assert "without requiring prior preflight review" in instructions


def test_task_reviewer_requires_gate_evidence_after_short_path_implementation() -> None:
    instructions = load_agent()["developer_instructions"]

    assert "post-implementation short-path review" in instructions
    assert "approved short-path task" in instructions
    assert "recorded preflight gate evidence" in instructions


def test_task_reviewer_cannot_modify_or_extend_the_review() -> None:
    instructions = load_agent()["developer_instructions"]

    assert "Do not edit files" in instructions
    assert "Do not run tests" in instructions
    assert "Do not spawn subagents" in instructions
    assert "read-only" in instructions
