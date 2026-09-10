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
            'display_name: "変更の出荷"',
            'short_description: "検証済み変更をコミット・プッシュ・MR・CIまで安全に進める"',
            'default_prompt: "変更をコミット、プッシュし、MRを開き、対象範囲内のCI失敗を解消するには $ship-change を使用してください。"',
        ),
        "post-merge-cleanup": (
            'display_name: "マージ後のクリーンアップ"',
            'short_description: "マージ済みworkflowのworktreeとartifactを安全に片付ける"',
            'default_prompt: "このworkflowの所有リソースのマージを確認し、安全に削除するには $post-merge-cleanup を使用してください。"',
        ),
        "execute-and-ship": (
            'display_name: "実行して出荷"',
            'short_description: "計画を実装しコミット・プッシュ・MR・CIまで連続して進める"',
            'default_prompt: "レビュー済み計画を実行し、MR対応可能なCIまで継続するには $execute-and-ship を使用してください。"',
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
        assert "明示" in body


def test_ship_change_requires_authorization_and_snapshot_gates() -> None:
    body = read(skill("ship-change") / "SKILL.md")
    for phrase in (
        "出荷認可",
        "LOCAL_COMPLETE",
        "execute-and-ship` の引き継ぎ",
        "開始時または再開時",
        "snapshot",
        "コミット",
        "remote",
        "MR",
        "CI",
        "allowlist",
        "external dirty",
        "レビュー済み",
        "検証済み",
        "staged",
        "controller",
        "論理",
        "固定されたdefault branch",
        "リポジトリの状態",
        "意図した",
        "base/head",
        "secret",
        "ローカルpath",
        "内部",
        "workflow artifact",
        "fail closed",
        "汚染の疑い",
        "コミット前",
        "対象範囲内",
        "エスカレーション",
        "マージ（`no merge`）",
        "no merge",
        "認証情報",
        "本番",
        "リリース",
        "タグ付け",
    ):
        assert phrase in body, phrase


def test_ship_change_resume_and_stop_contract_is_unambiguous() -> None:
    body = read(skill("ship-change") / "SKILL.md")
    for phrase in (
        "再計算",
        "ステージの直前",
        "preflight",
        "indexに対して",
        "コミット直前",
        "介在する変更なし",
        "完全一致",
        "不一致",
        "無効にして停止",
        "プッシュやMR作成を重複させない",
        "MR作成を重複させない",
        "外部ブロッカー",
        "スコープ拡大",
        "protected contract",
        "権限",
        "runner",
        "停止",
    ):
        assert phrase in body, phrase


def test_cleanup_requires_merge_ownership_exact_command_and_git_confirmation() -> None:
    body = read(skill("post-merge-cleanup") / "SKILL.md")
    reference = read(
        ROOT / "dot_codex/workflows/software_delivery/references/post-merge-cleanup.md"
    )
    for phrase in (
        "明示的",
        "merged",
        "所有権",
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
        "次のskillがない",
    ):
        assert phrase in body or phrase in reference, phrase

    assert "cleanup_result.py" not in body
    assert "branch_outcome" not in body


def test_cleanup_fails_closed_and_keeps_the_artifact() -> None:
    body = read(skill("post-merge-cleanup") / "SKILL.md")
    for phrase in (
        "保持",
        "not_attempted",
        "deferred",
        "無効なJSON",
        "不一致",
        "保持",
        "保留",
        "削除しない",
        "remote branchの削除はこの引き継ぎの範囲外なので削除しない",
        "ARTIFACT_REMOVE` へ進めたり",
        "`WT_REMOVE` がこのphaseのterminal state",
    ):
        assert phrase in body, phrase


def test_execute_and_ship_only_composes_execution_and_shipping() -> None:
    body = read(skill("execute-and-ship") / "SKILL.md")
    for phrase in (
        "出荷認可",
        "execute-plan",
        "ship-change",
        "ローカル検証",
        "MR対応可能なCI",
        "コミット",
        "プッシュ",
        "MR",
        "対象範囲内",
        "含めず",
        "discovery",
        "planning",
        "マージ",
        "クリーンアップ",
        "リリース",
        "タグ",
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
