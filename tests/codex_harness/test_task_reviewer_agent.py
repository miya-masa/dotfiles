from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "dot_codex/agents/task-reviewer.toml"


def load_agent() -> dict:
    with AGENT.open("rb") as agent_file:
        return tomllib.load(agent_file)


def test_task_reviewer_is_a_luna_low_read_only_reviewer() -> None:
    agent = load_agent()

    assert agent["name"] == "task-reviewer"
    assert "bounded" in agent["description"]
    assert "model" not in agent
    assert "model_reasoning_effort" not in agent
    assert agent["sandbox_mode"] == "read-only"


def test_task_reviewer_contract_keeps_verdicts_and_packet_bounded() -> None:
    instructions = load_agent()["developer_instructions"]
    instruction_lines = instructions.splitlines()

    assert len(instruction_lines) <= 15
    assert "bounded packet" in instructions
    assert "Spec compliance" in instructions
    assert "Simplicity" in instructions
    assert "分け" in instructions
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
    assert "事前のpreflight reviewを要求せず" in instructions


def test_task_reviewer_requires_gate_evidence_after_short_path_implementation() -> None:
    instructions = load_agent()["developer_instructions"]

    assert "実装後のshort-path review" in instructions
    assert "承認済みshort-path task" in instructions
    assert "記録済みpreflight gate evidence" in instructions


def test_task_reviewer_cannot_modify_or_extend_the_review() -> None:
    instructions = load_agent()["developer_instructions"]

    assert "ファイルを編集せず" in instructions
    assert "テスト、ビルド、lint、fetch" in instructions
    assert "subagentを起動しない" in instructions
    assert "読み取り専用" in instructions
