"""削除済み skill と Superpowers plugin への dangling 参照の走査 (spec A18/A19)."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).name

SCAN_SUFFIXES = {".md", ".py", ".json", ".sh", ".tmpl", ".toml", ".yaml"}
# spec A18 の除外は repo 直下の `docs/` (過去 artifact) と `.superpowers/`。
EXCLUDED_TOP_DIRS = {"docs", ".superpowers"}
EXCLUDED_DIRS = {".git", "__pycache__", ".aidocs"}
# 旧 skill 名 / plugin skill 名を negative assertion として意図的に書く検証コードだけ外す。
EXCLUDED_FILES = {SELF, "test_agents.py"}

# A18: 削除した workflow skill 名。`skills/<name>` 形式の path 参照と、
# 単体でバッククォート引用した skill 参照だけを見る (implementation-planning や
# ship-change のような新 skill 名に巻き込まれないよう語境界を要求する)。
DELETED = (
    "spec-review",
    "plan-review",
    "impl-review",
    "implementation",
    "verification",
    "ship",
    "postimpl-cleanup",
)
# `skills/<name>` `commands/<name>` に加え、旧 idiom の相対リンク `../<name>/` も見る。
DELETED_PATH_RE = re.compile(
    rf"(?:(?:skills|commands)/|\.\./)(?:{'|'.join(DELETED)})(?![-\w])"
)
DELETED_MENTION_RE = re.compile(rf"`(?:{'|'.join(DELETED)})`")
SLASH_COMMAND_RE = re.compile(r"/postimpl-cleanup(?![-\w])")

# A19: Superpowers plugin skill。prefix 付きと素名の両方を見る。
PLUGIN_PREFIX_RE = re.compile(r"superpowers:")
PLUGIN_BARE_RE = re.compile(
    r"(?<![-\w])(?:brainstorming|writing-plans|executing-plans|test-driven-development"
    r"|verification-before-completion|finishing-a-development-branch)(?![-\w])"
)

WORKFLOW_SCAN_PATHS = (
    "dot_claude/skills/product-discovery",
    "dot_claude/skills/implementation-planning",
    "dot_claude/skills/execute-plan",
    "dot_claude/skills/ship-change",
    "dot_claude/skills/execute-and-ship",
    "dot_claude/skills/post-merge-cleanup",
    "dot_agents/skills/start",
    "dot_agents/skills/bugfix",
    "dot_agents/skills/investigation",
    "dot_agents/skills/handoff",
    "dot_agents/workflows",
    "dot_claude/agents",
    "dot_claude/skills/codex-doublecheck",
)

DANGLING_SCAN_PATHS = (
    "dot_claude",
    "dot_agents",
    ".chezmoiscripts",
    "tests",
    "README.md",
    "CLAUDE.md",
)


def iter_files(relative: str):
    target = ROOT / relative
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        parts = path.relative_to(ROOT).parts
        if parts[0] in EXCLUDED_TOP_DIRS:
            continue
        if EXCLUDED_DIRS & set(parts):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        yield path


def scan(
    paths, pattern: re.Pattern[str], skip: re.Pattern[str] | None = None
) -> list[str]:
    hits = []
    for relative in paths:
        for path in iter_files(relative):
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if skip is not None and skip.search(line):
                    continue
                if pattern.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    return hits


def test_a18_no_dangling_reference_to_removed_workflow_skills() -> None:
    assert not scan(DANGLING_SCAN_PATHS, DELETED_PATH_RE)
    assert not scan(DANGLING_SCAN_PATHS, DELETED_MENTION_RE)
    assert not scan(DANGLING_SCAN_PATHS, SLASH_COMMAND_RE)


def test_scan_actually_covers_the_reference_update_targets() -> None:
    """走査自身の盲点検出。除外条件が広がって対象を素通りしていないことを固定する。"""
    scanned = {str(path.relative_to(ROOT)) for path in iter_files("dot_claude")}

    assert "dot_claude/skills/codex-doublecheck/SKILL.md" in scanned
    assert "dot_claude/agents/reviewer.md" in scanned

    # 旧 idiom の相対リンクと、stage 語彙に紛れた skill 参照を実際に検出できる。
    assert DELETED_PATH_RE.search("[x](../spec-review/references/review-common.md)")
    assert DELETED_MENTION_RE.search("体制は `impl-review` に従う")


def test_a18_removed_skill_sources_are_gone() -> None:
    for name in (
        "spec-review",
        "plan-review",
        "impl-review",
        "implementation",
        "verification",
        "ship",
    ):
        assert not (ROOT / "dot_agents/skills" / name).exists()
        assert not (ROOT / "dot_claude/skills" / f"symlink_{name}").exists()
    assert not (ROOT / "dot_claude/commands/postimpl-cleanup.md").exists()
    assert not (ROOT / "tests/dev_workflow/test_workflow_skills.py").exists()


def test_a20_chezmoi_remove_lists_retired_workflow_skills() -> None:
    """実機残骸の列挙。`.agents/` 側を消し損ねると Codex が旧 skill を auto-load する。"""
    remove = (ROOT / ".chezmoiremove").read_text(encoding="utf-8").splitlines()

    for name in (
        "spec-review",
        "plan-review",
        "impl-review",
        "implementation",
        "verification",
        "ship",
    ):
        assert f".agents/skills/{name}" in remove
        assert f".claude/skills/{name}" in remove
    assert ".claude/commands/postimpl-cleanup.md" in remove
    assert ".codex/workflows/software_delivery/scripts" in remove


def test_a19_workflow_has_no_superpowers_plugin_reference() -> None:
    assert not scan(WORKFLOW_SCAN_PATHS, PLUGIN_PREFIX_RE)
    assert not scan(WORKFLOW_SCAN_PATHS, PLUGIN_BARE_RE)


def test_shared_review_core_is_in_place() -> None:
    references = ROOT / "dot_agents/workflows/software_delivery/references"

    assert {path.name for path in references.glob("*.md")} == {
        "review-common.md",
        "analysis-techniques.md",
        "review-lenses.md",
    }
    lenses = (references / "review-lenses.md").read_text(encoding="utf-8")
    for lens in ("Completeness", "Soundness", "Operability", "Adversarial"):
        assert lens in lenses
    for lens in ("Correctness", "Robustness", "Security", "Contract", "Holistic"):
        assert lens in lenses
    assert "Spec compliance" in lenses
