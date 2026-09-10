"""Task 7 contract tests for the execute-plan phase skill."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "dot_codex/skills/execute-plan"
BODY = SKILL / "SKILL.md"
METADATA = SKILL / "agents/openai.yaml"
REFERENCE = ROOT / "dot_codex/workflows/software_delivery/references/task-execution.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_metadata_allows_recorded_execution_intent() -> None:
    content = read(METADATA)
    for expected in (
        'display_name: "計画実行"',
        'short_description: "計画を実装しリスクに応じたレビューとローカル検証で完了する"',
        'default_prompt: "レビュー済み計画を実装し、ローカル検証後に停止するには $execute-plan を使用してください。"',
        "policy:\n  allow_implicit_invocation: true",
    ):
        assert expected in content


def test_skill_is_concise_and_routes_the_execution_boundaries() -> None:
    body = read(BODY)
    assert len(body.splitlines()) <= 65
    assert "TODO" not in body
    for phrase in (
        "レビュー済み計画",
        "短縮経路タスク",
        "context.json",
        "wt switch --create <branch> --base <default> --no-cd --format=json",
        "absolute workdir",
        "OPTIONAL_DELEGATION",
        "逐次依存",
        "RED",
        "minimal GREEN",
        "limited refactor",
        "非挙動設定",
        "canonical risk matrix",
        "同じscope",
        "fresh 上位モデル / high",
        "snapshot",
        "LOCAL_COMPLETE",
        "コミットせず",
        "ship-change",
        "review-policy.md",
    ):
        assert phrase in body or phrase in read(REFERENCE), phrase


def test_reference_covers_tdd_reviews_resume_and_evidence_gates() -> None:
    reference = read(REFERENCE)
    for phrase in (
        "開始とresumeのゲート",
        "artifact",
        "Git証拠",
        "最初の未完了gate",
        "完了したtask",
        "redispatchしません",
        "未完了のreview",
        "未完了のverification",
        "欠落",
        "不整合",
        "wt switch --create <branch> --base <default> --no-cd --format=json",
        "absolute",
        "planの順序どおり",
        "RED",
        "RED reason",
        "minimal GREEN",
        "limited refactor",
        "挙動変更を非挙動と扱ってはいけません",
        "canonical risk",
        "Finding",
        "同じsnapshot gate",
        "異なるfixが2回失敗",
        "debugging",
        "最終review",
        "上位モデル",
        "review snapshot",
        "独立Risk trigger",
        "ローカル検証",
        "LOCAL_COMPLETE",
        "commit",
        "ship-change",
        "停止",
    ):
        assert phrase in reference, phrase


def test_reference_preserves_snapshot_binding_and_no_commit_boundary() -> None:
    reference = read(REFERENCE)
    for phrase in (
        "同じsnapshot",
        "review_snapshot_id",
        "固定したmerge-base",
        "reviewとローカル",
        "ローカル検証",
        "commitは作成せず",
        "shipping authorization",
        "次のphase",
    ):
        assert phrase in reference, phrase
