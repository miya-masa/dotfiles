from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS = (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8")
EFFORT_POLICY = (ROOT / "dot_agents/workflows/software_delivery/references/effort-policy.md").read_text(encoding="utf-8")
REVIEW_POLICY = (ROOT / "dot_codex/review-policy.md").read_text(encoding="utf-8")
DISCOVERY = (ROOT / "dot_codex/skills/product-discovery/SKILL.md").read_text(encoding="utf-8")
PLANNING = (ROOT / "dot_codex/skills/implementation-planning/SKILL.md").read_text(encoding="utf-8")
EXECUTE = (ROOT / "dot_codex/skills/execute-plan/SKILL.md").read_text(encoding="utf-8")
SHIPPING = (ROOT / "dot_codex/skills/execute-and-ship/SKILL.md").read_text(encoding="utf-8")


def test_optional_failure_falls_back_only_after_reclassification() -> None:
    compact = " ".join((AGENTS + DISCOVERY + EXECUTE).split())
    assert "optional" in compact.lower()
    assert "再確認" in compact
    assert "Controller直行へfallback" in compact


def test_mandatory_specialist_and_reviewer_failures_are_fail_closed() -> None:
    compact = " ".join((AGENTS + DISCOVERY + PLANNING + EXECUTE).split()).lower()
    for role in ("specification", "planning", "debugging", "reviewer"):
        assert role in compact
    for failure in ("unavailable", "insufficient", "conflicting", "boundary-widening"):
        assert failure in compact
    assert "fail closed" in compact or "fail-closed" in compact
    assert "narrow" in compact and "redispatch" in compact


def test_no_fixed_agent_count_contract_remains() -> None:
    combined = "\n".join((DISCOVERY, PLANNING, EXECUTE))
    for stale in ("要求の明確さにかかわらず必ず", "原則2体", "未完了タスクごとに、計画順で新しいLuna"):
        assert stale not in combined
    assert combined.count("canonical risk matrix") >= 3


def test_artifact_state_approval_shipping_and_stable_ids_remain_compatible() -> None:
    combined = "\n".join((AGENTS, DISCOVERY, PLANNING, EXECUTE, SHIPPING))
    for phrase in ("context.json", "D<n>", "AC<n>", "shipping authority", "approved scope", "コミットせず"):
        assert phrase in combined


def test_routing_keeps_controller_thin_and_separates_plan_gaps_from_hard_implementation() -> None:
    policy = EFFORT_POLICY
    assert "Controller は薄く広く" in policy
    for phrase in ("下位モデルへ実装", "fresh な上位モデル", "計画不足", "実装固有", "昇格で隠さない"):
        assert phrase in policy
    for phrase in ("通常実装はworkerへ渡す", "委譲コストが作業を上回る小変更", 'fork_turns="none"', "`model`", "`reasoning_effort`"):
        assert phrase in AGENTS
    for phrase in ("計画不足", "上位workerへ昇格", "decision-completeな通常実装はfresh `worker`"):
        assert phrase in EXECUTE


def test_codex_stage_model_effort_and_review_defaults_are_explicit() -> None:
    for phrase in (
        "gpt-5.6-luna` / `max",
        "gpt-5.6-terra` / `high",
        "gpt-5.6-sol` / `high",
        "gpt-6-astra` / `high",
        "fallback は `gpt-5.6-sol` / `medium`",
        "全段階を順番に実行せず",
        "Solの後に定例のAstraを追加しない",
    ):
        assert phrase in EFFORT_POLICY
    for phrase in (
        "normalでは `gpt-5.6-sol` / `high`",
        "影響範囲・不確実性からControllerが `gpt-6-astra` / `high`",
        "independent-risk`、fresh `gpt-6-astra` / `high` reviewer 2体",
        "`high`、fresh `gpt-6-astra` / `high` reviewer 1体",
        "reviewer 0、Controller self-check",
    ):
        assert phrase in REVIEW_POLICY


def test_planning_uses_specialist_but_does_not_recreate_existing_decisions() -> None:
    assert "通常の計画作成はfreshな上位モデルの`planning`へ渡し" in PLANNING
    assert "既存決定の機械的な転記だけ" in PLANNING
    assert "重要な実装案が複数" in PLANNING
    assert "mandatory" in PLANNING


def test_normal_single_task_uses_one_fixed_snapshot_review() -> None:
    assert "単一`review_snapshot_id`" in EXECUTE
    assert "canonical risk matrixを1回適用" in EXECUTE
    assert "重複起動しない" in EXECUTE


def test_code_snapshot_change_invalidates_review_and_validation_completely() -> None:
    for component in ("content", "mode", "deletion", "base", "allowlist"):
        assert component in EXECUTE
    assert "reviewとlocal validationを全面無効化" in EXECUTE


def test_parallel_delegation_requires_independent_bounded_nonshared_workstreams() -> None:
    compact = " ".join((AGENTS + EXECUTE).split())
    for phrase in ("独立context", "bounded packet", "逐次依存", "shared mutable resource", "並列write"):
        assert phrase in compact


def test_resume_preserves_committed_gates_and_applies_matrix_at_first_incomplete_gate() -> None:
    reference = (ROOT / "dot_codex/workflows/software_delivery/references/task-execution.md").read_text(encoding="utf-8")
    for phrase in ("最初の未完了gate", "完了したtaskは決してredispatchしません", "commit済みcontext revision", "canonical risk"):
        assert phrase in reference


def test_adaptive_execution_does_not_expand_shipping_authority() -> None:
    compact = " ".join(SHIPPING.split())
    for phrase in ("shipping_authorized: true", "限定されたコミット", "スコープ拡大を決して許可しない"):
        assert phrase in compact


def test_diagnosis_is_read_only_but_requested_eligible_fix_can_follow() -> None:
    diagnosis = (ROOT / "dot_codex/skills/systematic-debugging/SKILL.md").read_text(encoding="utf-8")
    assert "このskillではコードを変更しない" not in diagnosis
    assert "診断段階と debugging agent はコードを変更しない" in diagnosis
    for phrase in ("修正も依頼され", "直接完了条件", "診断 brief を確定", "修正段階へ移り", "targeted validation"):
        assert phrase in diagnosis


def test_existing_implementation_intent_enters_execution_without_shipping() -> None:
    for runtime in ("dot_codex", "dot_claude"):
        execution = (ROOT / runtime / "skills/execute-plan/SKILL.md").read_text(encoding="utf-8")
        for phrase in ("context.json", "記録済み", "既存の明示的な実装依頼", "未承認 spec からは実装しない", "LOCAL_COMPLETE"):
            assert phrase in execution
    for phase in ("ship-change", "execute-and-ship"):
        metadata = (ROOT / "dot_codex/skills" / phase / "agents/openai.yaml").read_text(encoding="utf-8")
        assert "allow_implicit_invocation: false" in metadata


def test_top_level_instructions_do_not_bypass_normal_worker_routing() -> None:
    claude = (ROOT / "dot_claude/CLAUDE.md").read_text()
    assert "通常実装はworkerへ渡す" in AGENTS
    assert "直接完了の可否は共通方針の条件" in AGENTS
    assert "protected contract 非該当なら、複数ファイルでも直接完了" not in claude
    assert "委譲コストが作業を上回る小変更だけ、ファイル数を問わず直接完了" in claude
