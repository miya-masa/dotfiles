from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_codex_uses_dedicated_instructions_and_three_stage_skills() -> None:
    agents = ROOT / "dot_codex/AGENTS.md"
    skills_root = ROOT / "dot_codex/skills"
    expected_skills = {
        "product-discovery",
        "software-delivery",
        "systematic-debugging",
    }

    assert agents.is_file()
    assert not agents.is_symlink()
    assert {
        path.name for path in skills_root.iterdir() if path.is_dir()
    } == expected_skills
    for name in expected_skills:
        skill = skills_root / name / "SKILL.md"
        metadata = skills_root / name / "agents/openai.yaml"
        assert skill.is_file()
        assert metadata.is_file()
        assert len(skill.read_text(encoding="utf-8").splitlines()) <= 65
        metadata_lines = metadata.read_text(encoding="utf-8").splitlines()
        assert metadata_lines[0] == "interface:"
        interface = dict(
            line.removeprefix("  ").split(': "', maxsplit=1)
            for line in metadata_lines[1:]
        )
        interface = {key: value.removesuffix('"') for key, value in interface.items()}
        assert set(interface) == {"display_name", "short_description", "default_prompt"}
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${name}" in interface["default_prompt"]
    assert not (ROOT / "dot_codex/symlink_AGENTS.md").exists()


def test_codex_skills_have_distinct_handoff_boundaries() -> None:
    skills_root = ROOT / "dot_codex/skills"
    discovery = (skills_root / "product-discovery/SKILL.md").read_text(encoding="utf-8")
    debugging = (skills_root / "systematic-debugging/SKILL.md").read_text(encoding="utf-8")
    delivery = (skills_root / "software-delivery/SKILL.md").read_text(encoding="utf-8")

    assert "コードを変更しない" in discovery
    assert "software-delivery" in discovery
    assert "root cause" in debugging
    assert "コードを変更しない" in debugging
    assert "software-delivery" in debugging
    assert "product-discovery" in delivery
    assert "systematic-debugging" in delivery
    assert "仕様探索や原因調査だけの依頼には使わない" in delivery


def test_codex_workflows_share_artifact_review_policy() -> None:
    policy = (ROOT / "dot_codex/review-policy.md").read_text(encoding="utf-8")
    agents = (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8")
    skill_texts = [
        path.read_text(encoding="utf-8")
        for path in (ROOT / "dot_codex/skills").glob("*/SKILL.md")
    ]

    assert "review-policy.md" in agents
    assert all("review-policy.md" in text for text in skill_texts)
    for artifact in ("仕様brief", "診断brief", "実行計画", "コード"):
        assert artifact in policy
    for tier in ("軽微", "通常", "高リスク"):
        assert tier in policy
    assert "Correctness / Adversarial" in policy
    assert "Contract / Product-fit / Simplicity" in policy
    assert "最大3件" in policy
    assert "到達可能" in policy
    assert "production codeとtest" in policy


def test_only_concise_read_only_reviewer_is_customized() -> None:
    agent_files = list((ROOT / "dot_codex/agents").glob("*.toml"))

    assert [path.name for path in agent_files] == ["reviewer.toml"]
    with agent_files[0].open("rb") as agent_file:
        reviewer = tomllib.load(agent_file)
    assert reviewer["sandbox_mode"] == "read-only"
    assert "model" not in reviewer
    assert "model_reasoning_effort" not in reviewer
    assert len(reviewer["developer_instructions"].splitlines()) <= 20
    assert "review-policy.md" in reviewer["developer_instructions"]
    assert "speculative hardening" in reviewer["developer_instructions"]


def test_deprecated_codex_harness_files_are_absent() -> None:
    assert not (ROOT / "dot_local/bin/executable_codex-worker").exists()
    assert not (ROOT / "tests/codex_harness/test_dispatcher.py").exists()
    assert not list((ROOT / "dot_codex/skills").glob("symlink_*"))


def test_repository_docs_describe_the_native_codex_harness() -> None:
    docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("README.md", "CLAUDE.md")
    )

    assert "software-delivery" in docs
    assert "native subagents" in docs
    assert "Codex Superpowers" not in docs
    assert "custom `agent-*`" not in docs
