"""Semantic contracts for the Codex product-discovery entry flow."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "dot_codex/skills/product-discovery/SKILL.md"
AGENTS = ROOT / "dot_codex/AGENTS.md"
SPEC = ROOT / "dot_codex/workflows/software_delivery/references/spec-and-plan.md"
RECOVERY = ROOT / "dot_codex/workflows/software_delivery/references/state-recovery.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(body: str, heading: str, next_heading: str) -> str:
    start = body.index(heading)
    end = body.index(next_heading, start + len(heading))
    return body[start:end]


def test_clear_discovery_allows_controller_direct_without_agents() -> None:
    body = read(SKILL)
    entry = section(body, "## 開始", "## 対話")
    conversation = section(body, "## 対話", "## 短縮経路")

    ordered = ("new-id", "init", "validate", "DISCOVERY")
    positions = [entry.index(value) for value in ordered]
    assert positions == sorted(positions)
    direct_rule = next(line for line in conversation.splitlines() if "DIRECT / OPTIONAL_DELEGATION" in line)
    assert "既存決定の転記はController" in direct_rule
    assert "実質的な仕様検討" in direct_rule and "`specification`へ渡す" in direct_rule


def test_ambiguous_or_protected_discovery_requires_specification_and_fails_closed() -> None:
    conversation = section(read(SKILL), "## 対話", "## 短縮経路")
    mandatory = next(line for line in conversation.splitlines() if "上位モデル / high `specification`" in line)
    for phrase in ("複数", "未定義", "protected-contract", "上位モデル / high `specification`", "stop", "narrow redispatch"):
        assert phrase.lower() in mandatory.lower(), phrase


def test_resume_selection_is_explicit_nonterminal_and_single_writer() -> None:
    skill_resume = section(read(SKILL), "## 再開", "## 対話")
    recovery_resume = section(
        read(RECOVERY),
        "## discoveryの選択と逐次resume",
        "## CLI契約",
    )

    resume_lower = skill_resume.lower()
    for phrase in (
        "新規リクエスト",
        "terminal",
        "explicit exact workflow ID/path",
        "single unambiguous nonterminal",
        "複数候補",
        "ユーザーに1回だけ選択",
        "first incomplete committed gate",
        "prior `controller`",
        "live `controller`",
    ):
        assert phrase.lower() in resume_lower, phrase

    recovery_lower = " ".join(recovery_resume.lower().split())
    assert "別controllerが liveである証拠があれば継続を拒否します" in recovery_lower
    assert "concurrent controllerはunsupported" in recovery_lower
    assert "multi-writer検出やlock protocolを追加しません" in recovery_lower


def test_fresh_short_path_initializes_artifact_before_draft_and_preflight() -> None:
    body = read(SKILL)
    entry = section(body, "## 開始", "## 再開")
    short_path = section(body, "## 短縮経路", "## 停止")
    resume = section(body, "## 再開", "## 対話")

    entry_lower = " ".join(entry.lower().split())
    for phrase in ("正式 workflow の新規リクエスト（通常または短縮）", "通常または短縮", "new-id", "init", "validate", "discovery", "revision `0`"):
        assert phrase in entry_lower, phrase
    entry_order = [
        entry_lower.index("new-id"),
        entry_lower.index("init"),
        entry_lower.index("validate"),
        entry_lower.index("discovery"),
        entry_lower.index("revision `0`"),
    ]
    assert entry_order == sorted(entry_order)
    assert "規範判断の前に" in entry_lower

    short_lower = " ".join(short_path.lower().split())
    for phrase in ("validated artifact", "controller検査", "canonical risk matrix"):
        assert phrase in short_lower, phrase
    short_order = [
        short_lower.index("validated artifact"),
        short_lower.index("controller検査"),
        short_lower.index("canonical risk matrix"),
    ]
    assert short_order == sorted(short_order)

    resume_lower = " ".join(resume.lower().split())
    assert "新規リクエスト" in resume_lower and "terminal artifact" in resume_lower
    assert "自動再開" in resume_lower


def test_short_path_requires_affirmative_evidence_and_returns_to_specification() -> None:
    body = read(SKILL)
    short_path = section(body, "## 短縮経路", "## 停止")

    short_path_lower = short_path.lower()
    for phrase in (
        "affirmative evidence",
        "canonical risk matrix",
        "ambiguity",
        "missing evidence",
        "boundary",
        "protected-contract",
        "Important",
        "execution choice` を保留",
        "上位モデルの `specification`",
    ):
        assert phrase.lower() in short_path_lower, phrase
    fallback = short_path_lower[short_path_lower.index("ambiguity") :]
    assert "上位モデルの `specification` path" in fallback


def test_short_path_choices_add_shipping_authority_without_expanding_scope() -> None:
    body = read(SKILL)
    short_path = section(body, "## 短縮経路", "## 停止")
    choice_line = next(line for line in short_path.splitlines() if "execute-plan" in line)
    choice_lower = choice_line.lower()

    for phrase in (
        "execute-plan",
        "execute-and-ship",
        "shipping authority",
        "approved scope",
    ):
        assert phrase in choice_lower, phrase
    assert choice_lower.index("execute-plan") < choice_lower.index("execute-and-ship")
    assert choice_lower.index("shipping authority") < choice_lower.index("approved scope")
    assert "だけ" in choice_lower
    assert "拡大しない" in choice_lower


def test_stop_records_simplicity_finding_outcomes_without_user_escalation() -> None:
    body = read(SKILL)
    stop = body[body.index("## 停止") :]
    stop_rule = next(line for line in stop.splitlines() if "Simplicity finding" in line)
    stop_lower = stop_rule.lower()

    for phrase in (
        "findingなし",
        "「指摘なし」",
        "代替案finding",
        "`却下（根拠付き）`",
        "`ユーザー判断`へ上げない",
    ):
        assert phrase.lower() in stop_lower, phrase
    assert stop_lower.index("findingなし") < stop_lower.index("「指摘なし」")
    assert stop_lower.index("代替案finding") < stop_lower.index("`却下（根拠付き）`")
    assert stop_lower.index("`却下（根拠付き）`") < stop_lower.index("`ユーザー判断`へ上げない")


def test_mandatory_specialist_failure_is_fail_closed() -> None:
    body = read(AGENTS)
    routing = section(body, "## Routing", "## Delegation contract")

    routing_lower = routing.lower()
    for phrase in (
        "mandatory specialist",
        "unavailable",
        "insufficient",
        "conflicting",
        "boundary-widening",
        "stop",
        "narrower",
        "redispatch",
        "Terra",
        "no substitute",
    ):
        assert phrase.lower() in routing_lower, phrase
    assert "high-impact decision" in routing_lower


def test_review_contract_uses_canonical_risk_matrix_without_fixed_phase_count() -> None:
    body = read(SPEC)
    review = section(body, "### 仕様review", "## planning packetとplan")
    review = " ".join(review.split())

    for phrase in (
        "canonical risk matrix",
        "minor",
        "normal/high",
        "独立Risk trigger",
        "phase名やartifact名だけで人数を固定しません",
        "Completeness",
        "Simplicity",
        "公開APIや一般的な後方互換性",
        "適用可能な具体的checklist",
        "state authority",
        "state authorityとtransition",
        "integration seam",
        "invariant",
        "partial failure",
        "resume/retry",
        "observability",
        "rollout",
        "migration",
        "recovery",
        "割り当てたlensごとに結果を分けて返します",
    ):
        assert phrase in review, phrase


def test_product_decisions_are_promoted_only_when_outcomes_need_user_judgment() -> None:
    discovery = section(read(SPEC), "## discovery packetと仕様", "## 安定したdecision")
    compact = " ".join(discovery.split())

    for phrase in (
        "repository evidence",
        "一意に導けない",
        "観測できる結果",
        "protected contract",
        "productの価値判断",
        "既存挙動の継承",
        "accepted non-goal",
        "generator/frameworkの標準挙動",
        "implementation note",
        "`D<n>`やopen decisionを作りません",
        "依存するproduct decision",
        "原則1問",
        "独立したdecision",
        "最大3件まで一括確認",
    ):
        assert phrase in compact, phrase

    skill = " ".join(read(SKILL).split())
    for phrase in (
        "3条件をすべて満たすproduct decision",
        "productの価値判断またはユーザーの優先順位が必要",
    ):
        assert phrase in skill, phrase


def test_closure_review_is_bounded_by_changed_ids_and_dependencies() -> None:
    review = section(read(SPEC), "### 変更後のclosure review", "## acceptanceの追跡性")
    compact = " ".join(review.split())

    for phrase in (
        "意味を変えない表現変更",
        "reviewerは起動しない",
        "boundedな修正",
        "変更ID",
        "dependency cone",
        "依存関係を推移的に辿り",
        "結果が変わらないと証明できた地点で探索を止め",
        "`D1 -> D2 -> AC3 / Surface A`なら末端まで含め",
        "到達不能な`D4`は含めません",
        "未変更の独立した領域を再reviewしません",
        "追加final checkは起動しません",
        "spec review全体を無効化",
        "progress.md",
    ):
        assert phrase in compact, phrase


def test_external_surface_agreement_gate_is_required_before_approval() -> None:
    surface = section(read(SPEC), "## 外部サーフェス合意", "## 短縮経路")

    for phrase in (
        "`## 外部サーフェス`節を持たせます",
        "外部サーフェスの新設・変更・廃止なし",
        "新設 / 変更 / 廃止",
        "surface family",
        "区分",
        "主要な変更",
        "根拠",
        "判断可能な契約カード",
        "変更前",
        "変更後",
        "request / input",
        "response / output",
        "エラー・status・exit code",
        "認証認可",
        "互換性",
        "rollback / recovery",
        "正常例",
        "境界 / 失敗例",
        "派生artifact / 同期先",
        "generated client",
        "別familyに分けません",
        "draft",
        "presented",
        "agreed",
        "明示的一括承認",
        "`他は承認`などの明示があるときだけ",
        "明示がなければ`presented`を維持します",
        "変更対象とそのdependency coneだけを`draft`へ戻します",
        "個別合意必須",
        "通常の公開API変更や後方互換性だけを理由に個別合意必須にしません",
        "その他のfamilyを理由なく 一問一答にしません",
        "agreed でなければそれらへは進みません",
        "spec 承認の要求",
        "実行方法の選択の提示",
        "handoff",
        "session をまたぐ中断（compact を含む）",
        "保留",
        "中止",
    ):
        assert phrase in " ".join(surface.split()) or phrase in surface, phrase

    skill_body = read(SKILL)
    for phrase in ("外部サーフェス", "agreed", "spec-and-plan.md"):
        assert phrase in skill_body, phrase
    assert not any(
        "項目" in line and "区分" in line and "決めた内容" in line and "根拠" in line
        for line in skill_body.splitlines()
    )

    assert "mid-flow" not in surface


def test_product_discovery_entry_links_required_lifecycle_and_recovery_contracts() -> None:
    body = read(SKILL)
    entry = section(body, "## 開始", "## 対話")

    links = (
        "[spec-and-plan.md](../../workflows/software_delivery/references/spec-and-plan.md)",
        "[artifact-lifecycle.md](../../workflows/software_delivery/references/artifact-lifecycle.md)",
        "[state-recovery.md](../../workflows/software_delivery/references/state-recovery.md)",
    )
    positions = [entry.index(link) for link in links]
    assert positions == sorted(positions)
    assert "artifact 初期化の前に" in entry
    assert "必要な節だけ読む" in entry
    assert "既存 workflow ID / active AC" in entry
