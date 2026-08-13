from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_codex_uses_dedicated_instructions_and_phase_skills() -> None:
    agents = ROOT / "dot_codex/AGENTS.md"
    skills_root = ROOT / "dot_codex/skills"
    expected_skills = {
        "product-discovery",
        "implementation-planning",
        "execute-plan",
        "ship-change",
        "post-merge-cleanup",
        "execute-and-ship",
        "systematic-debugging",
    }

    assert agents.is_file()
    assert not agents.is_symlink()
    assert {
        path.name for path in skills_root.iterdir() if path.is_dir()
    } == expected_skills
    assert not (skills_root / "software-delivery").exists()
    for name in expected_skills:
        skill = skills_root / name / "SKILL.md"
        metadata = skills_root / name / "agents/openai.yaml"
        assert skill.is_file()
        assert metadata.is_file()
        assert len(skill.read_text(encoding="utf-8").splitlines()) <= 65
        metadata_text = metadata.read_text(encoding="utf-8")
        metadata_lines = metadata_text.splitlines()
        assert metadata_lines[0] == "interface:"
        interface = dict(
            line.removeprefix("  ").split(': "', maxsplit=1)
            for line in metadata_lines[1:]
            if line.startswith("  ") and ': "' in line
        )
        interface = {key: value.removesuffix('"') for key, value in interface.items()}
        assert set(interface) == {"display_name", "short_description", "default_prompt"}
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${name}" in interface["default_prompt"]
        if name != "systematic-debugging":
            assert "policy:\n  allow_implicit_invocation: false" in metadata_text
    assert not (ROOT / "dot_codex/symlink_AGENTS.md").exists()


def test_codex_instructions_avoid_zsh_readonly_status_variable() -> None:
    agents = (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8")

    assert "zsh" in agents
    assert "status" in agents
    assert "task_status" in agents


def test_codex_routes_routine_work_to_luna_and_judgment_to_sol() -> None:
    agents = (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8")
    planning = (ROOT / "dot_codex/skills/implementation-planning/SKILL.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "explorer",
        "worker",
        "specification",
        "planning",
        "debugging",
        "reviewer",
    ):
        assert expected in agents
    for expected in (
        'fork_turns="none"',
        "ユーザーの目的",
        "具体的な問い",
        "対象範囲",
        "既知の事実",
        "現在の仮定",
        "制約とnon-goal",
        "決定済み事項",
        "未解決事項",
        "ファイル変更の可否",
        "必要な成果物",
        "完了条件",
    ):
        assert expected in agents
    for expected in (
        "acceptance criteria",
        "owned paths",
        "検証command",
        "protected constraints",
        "stop条件",
        "2回失敗",
    ):
        assert expected in planning or expected in agents
    assert "重要な実装案が複数" in agents
    assert "要求の解釈が複数" in agents
    assert "推測なしに継続不能" in agents
    assert "実際のspawn tool callとagent ID/status" in agents
    assert "agent結果をcontrollerが代筆せず" in agents


def test_codex_skills_have_distinct_handoff_boundaries() -> None:
    skills_root = ROOT / "dot_codex/skills"
    discovery = (skills_root / "product-discovery/SKILL.md").read_text(encoding="utf-8")
    debugging = (skills_root / "systematic-debugging/SKILL.md").read_text(
        encoding="utf-8"
    )
    planning = (skills_root / "implementation-planning/SKILL.md").read_text(
        encoding="utf-8"
    )
    execution = (skills_root / "execute-plan/SKILL.md").read_text(encoding="utf-8")

    assert "コードやplanを変更しない" in discovery
    assert "implementation-planning" in discovery
    assert "software-delivery" not in discovery
    assert "root cause" in debugging
    assert "コードを変更しない" in debugging
    assert "implementation-planning" in debugging
    assert "software-delivery" not in debugging
    assert "product-discovery" in planning
    assert "execute-plan" in planning
    assert "execute-and-ship" in planning
    assert "ship-change" in execution
    assert "未確定のproduct判断や実装そのものには使わない" in planning


def test_codex_workflows_share_artifact_review_policy() -> None:
    policy = (ROOT / "dot_codex/review-policy.md").read_text(encoding="utf-8")
    agents = (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8")
    skill_texts = {
        path.parent.name: path.read_text(encoding="utf-8")
        for path in (ROOT / "dot_codex/skills").glob("*/SKILL.md")
    }

    assert "review-policy.md" in agents
    assert all(
        "review-policy.md" in text
        for name, text in skill_texts.items()
        if name != "execute-and-ship"
    )
    assert "review" in skill_texts["execute-and-ship"].lower()
    for artifact in ("仕様brief", "診断brief", "実行計画", "コード"):
        assert artifact in policy
    for tier in ("軽微", "通常", "高リスク"):
        assert tier in policy
    assert "Correctness / Robustness / Security" in policy
    assert "Contract / Product-fit / Simplicity" in policy
    assert "最大2つ" in policy
    for expected in (
        "一次証拠",
        "未検証事項",
        "具体的impact",
        "到達可能",
    ):
        assert expected in policy
    assert "最大3件" in policy
    assert "named `reviewer`" in policy


def test_native_agents_pin_models_to_their_roles() -> None:
    agent_files = sorted((ROOT / "dot_codex/agents").glob("*.toml"))

    assert [path.name for path in agent_files] == [
        "debugging.toml",
        "explorer.toml",
        "planning.toml",
        "reviewer.toml",
        "specification.toml",
        "task-reviewer.toml",
        "worker.toml",
    ]
    agents = {}
    for path in agent_files:
        with path.open("rb") as agent_file:
            agents[path.stem] = tomllib.load(agent_file)

    explorer = agents["explorer"]
    assert explorer["name"] == "explorer"
    assert explorer["model"] == "gpt-5.6-luna"
    assert explorer["model_reasoning_effort"] == "max"
    assert explorer["sandbox_mode"] == "read-only"
    assert len(explorer["developer_instructions"].splitlines()) <= 15

    worker = agents["worker"]
    assert worker["name"] == "worker"
    assert worker["model"] == "gpt-5.6-luna"
    assert worker["model_reasoning_effort"] == "max"
    assert worker["sandbox_mode"] == "workspace-write"
    assert len(worker["developer_instructions"].splitlines()) <= 15

    for role in ("debugging", "planning", "specification", "reviewer"):
        agent = agents[role]
        assert agent["model"] == "gpt-5.6-sol"
        assert agent["model_reasoning_effort"] == "high"
        assert agent["sandbox_mode"] == "read-only"
        assert len(agent["developer_instructions"].splitlines()) <= 35

    specification = agents["specification"]["developer_instructions"]
    assert "実装中立" in specification
    assert "acceptance criteria" in specification
    assert "コード、設定、外部状態を変更せず" in specification

    planning = agents["planning"]["developer_instructions"]
    assert "実装計画" in planning
    assert "completion criteria" in planning
    assert "rollout/migration/rollback" in planning

    reviewer = agents["reviewer"]["developer_instructions"]
    assert "review-policy.md" in reviewer
    assert "自己完結したpacket" in reviewer
    assert "反証" in reviewer
    assert "Finding" in reviewer
    assert "1パス" in reviewer
    assert "未検証事項" in reviewer
    for expected in (
        "severity",
        "confidence",
        "file/symbol/line",
        "具体的失敗scenario",
        "impact",
        "現在のtestで防げない理由",
        "修正方針",
        "必要な回帰test",
    ):
        assert expected in reviewer

    debugging = agents["debugging"]["developer_instructions"]
    assert "root cause" in debugging
    assert "競合仮説" in debugging
    assert "コード、test、設定、外部状態を変更せず" in debugging


def test_chezmoi_remove_preserves_managed_native_agents() -> None:
    remove = (ROOT / ".chezmoiremove").read_text(encoding="utf-8").splitlines()

    assert remove[:5] == [
        ".codex/agents/*.toml",
        "!.codex/agents/explorer.toml",
        "!.codex/agents/debugging.toml",
        "!.codex/agents/planning.toml",
        "!.codex/agents/reviewer.toml",
    ]
    assert remove[5:8] == [
        "!.codex/agents/specification.toml",
        "!.codex/agents/worker.toml",
        "!.codex/agents/task-reviewer.toml",
    ]
    assert ".codex/skills/software-delivery" in remove


def test_workflow_helpers_live_in_the_shared_core() -> None:
    shared = ROOT / "dot_agents/workflows/software_delivery/scripts"
    codex_scripts = ROOT / "dot_codex/workflows/software_delivery/scripts"

    assert not codex_scripts.exists()
    assert {path.name for path in shared.glob("*.py")} == {
        "workflow_state.py",
        "workflow_artifact.py",
        "review_snapshot.py",
    }

    cleanup_reference = (
        ROOT / "dot_codex/workflows/software_delivery/references/post-merge-cleanup.md"
    ).read_text(encoding="utf-8")
    assert "cleanup_result.py" not in cleanup_reference
    assert "dot_codex/workflows/software_delivery/scripts" not in cleanup_reference


def test_deprecated_codex_harness_files_are_absent() -> None:
    assert not (ROOT / "tests/codex_harness/test_dispatcher.py").exists()
    assert not list((ROOT / "dot_codex/skills").glob("symlink_*"))
    assert not (ROOT / "dot_codex/skills/software-delivery").exists()


def test_workflow_artifacts_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert gitignore.count("/.aidocs/") == 1


def test_repository_docs_describe_the_native_codex_harness() -> None:
    docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8") for path in ("README.md", "CLAUDE.md")
    )

    for expected in (
        "product-discovery",
        "implementation-planning",
        "execute-plan",
        "ship-change",
        "post-merge-cleanup",
        "execute-and-ship",
        "systematic-debugging",
    ):
        assert expected in docs
    assert "software-delivery" not in docs
    assert "native subagents" in docs
    assert "Codex Superpowers" not in docs
    assert "custom `agent-*`" not in docs
