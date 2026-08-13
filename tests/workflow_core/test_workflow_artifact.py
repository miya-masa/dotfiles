from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "dot_agents/workflows/software_delivery/scripts/workflow_artifact.py"
STATE_SCRIPT = ROOT / "dot_agents/workflows/software_delivery/scripts/workflow_state.py"


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    result = run_git(tmp_path, "init", "-q", "-b", "main")
    assert result.returncode == 0, result.stderr
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    assert run_git(tmp_path, "add", "README.md").returncode == 0
    assert (
        run_git(
            tmp_path,
            "-c",
            "user.name=Codex Test",
            "-c",
            "user.email=codex@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ).returncode
        == 0
    )
    return tmp_path


def run_cli(repo: Path, command: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), command, "--project-root", str(repo), *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def artifact_root(repo: Path, workflow_id: str = "demo-workflow") -> Path:
    return repo / ".aidocs" / "workflows" / workflow_id


def context_path(repo: Path, workflow_id: str = "demo-workflow") -> Path:
    return artifact_root(repo, workflow_id) / "context.json"


def init_artifact(
    repo: Path, workflow_id: str = "demo-workflow"
) -> subprocess.CompletedProcess[str]:
    return run_cli(repo, "init", "--workflow-id", workflow_id)


def test_new_id_is_bounded_and_normalized(git_repo: Path) -> None:
    result = run_cli(git_repo, "new-id", "A feature / with spaces")

    assert result.returncode == 0, result.stderr
    workflow_id = result.stdout.strip()
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", workflow_id)
    assert len(workflow_id) <= 63
    assert workflow_id.startswith("a-feature-with-spaces-")
    assert re.search(r"-[0-9]{14}-[0-9a-f]{8}$", workflow_id)


def test_init_creates_exact_tree_and_valid_context(git_repo: Path) -> None:
    result = init_artifact(git_repo)

    assert result.returncode == 0, result.stderr
    root = artifact_root(git_repo)
    assert {path.relative_to(root).as_posix() for path in root.rglob("*")} == {
        "spec.md",
        "plan.md",
        "progress.md",
        "context.json",
        "tasks",
        "reviews",
        "verification.md",
    }
    context = json.loads(context_path(git_repo).read_text(encoding="utf-8"))
    assert context["identity"] == {
        "schema_version": 1,
        "workflow_id": "demo-workflow",
        "source_root": str(git_repo.resolve()),
        "artifact_root": str(root.resolve()),
        "default_branch": "main",
        "base_commit": run_git(git_repo, "rev-parse", "HEAD").stdout.strip(),
    }
    assert context["state"] == {
        "phase": "DISCOVERY",
        "stopped_from": None,
        "artifact_revision": 0,
    }
    assert context["workspace"] == {"worktree_path": None, "branch": None}
    assert (
        subprocess.run(
            [
                sys.executable,
                str(STATE_SCRIPT),
                "validate",
                "--context",
                str(context_path(git_repo)),
            ],
            text=True,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def test_init_preserves_tracked_gitignore_and_adds_local_exclude_idempotently(
    git_repo: Path,
) -> None:
    tracked_gitignore = git_repo / ".gitignore"
    tracked_gitignore.write_text("*.local\n", encoding="utf-8")
    assert run_git(git_repo, "add", ".gitignore").returncode == 0
    assert (
        run_git(
            git_repo,
            "-c",
            "user.name=Codex Test",
            "-c",
            "user.email=codex@example.invalid",
            "commit",
            "-qm",
            "ignore",
        ).returncode
        == 0
    )
    before = tracked_gitignore.read_bytes()

    first = init_artifact(git_repo)
    assert first.returncode == 0, first.stderr
    assert tracked_gitignore.read_bytes() == before
    exclude = git_repo / ".git" / "info" / "exclude"
    assert exclude.read_text(encoding="utf-8").splitlines().count("/.aidocs/") == 1

    # A second workflow must not duplicate the repository-local ignore rule.
    second = init_artifact(git_repo, "another-workflow")
    assert second.returncode == 0, second.stderr
    assert exclude.read_text(encoding="utf-8").splitlines().count("/.aidocs/") == 1


@pytest.mark.parametrize(
    "workflow_id",
    ["../escape", "a/b", "/absolute", "", "-bad", "A_bad", "a" * 64],
)
def test_invalid_ids_do_not_mutate_repository(git_repo: Path, workflow_id: str) -> None:
    exclude = git_repo / ".git" / "info" / "exclude"
    before = exclude.read_bytes()
    result = init_artifact(git_repo, workflow_id)

    assert result.returncode != 0
    assert exclude.read_bytes() == before
    assert not (git_repo / ".aidocs").exists()


def test_colliding_id_is_rejected_without_mutation(git_repo: Path) -> None:
    first = init_artifact(git_repo)
    assert first.returncode == 0, first.stderr
    before = (git_repo / ".git" / "info" / "exclude").read_bytes()
    result = init_artifact(git_repo)

    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert (git_repo / ".git" / "info" / "exclude").read_bytes() == before


def test_symlink_ancestor_is_rejected_without_mutation(
    git_repo: Path, tmp_path: Path
) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (git_repo / ".aidocs").symlink_to(target, target_is_directory=True)
    before = (git_repo / ".git" / "info" / "exclude").read_bytes()

    result = init_artifact(git_repo)

    assert result.returncode != 0
    assert (git_repo / ".git" / "info" / "exclude").read_bytes() == before
    assert not (target / "workflows").exists()


def test_remove_requires_terminal_phase_exact_revision_and_root(git_repo: Path) -> None:
    assert init_artifact(git_repo).returncode == 0
    root = artifact_root(git_repo)
    context = json.loads(context_path(git_repo).read_text(encoding="utf-8"))
    before = context_path(git_repo).read_bytes()

    for args in (
        ("--expected-revision", "0", "--phase", "LOCAL_COMPLETE"),
        ("--expected-revision", "1", "--phase", "ARTIFACT_REMOVE"),
    ):
        result = run_cli(git_repo, "remove", "--workflow-id", "demo-workflow", *args)
        assert result.returncode != 0
        assert root.exists()
        assert context_path(git_repo).read_bytes() == before

    context["state"]["phase"] = "ARTIFACT_REMOVE"
    context_path(git_repo).write_text(
        json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    terminal_bytes = context_path(git_repo).read_bytes()
    wrong_root = git_repo.parent / "other"
    wrong_root.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "remove",
            "--project-root",
            str(wrong_root),
            "--workflow-id",
            "demo-workflow",
            "--expected-revision",
            "0",
            "--phase",
            "ARTIFACT_REMOVE",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert root.exists()
    assert context_path(git_repo).read_bytes() == terminal_bytes


def test_remove_requires_explicit_artifact_remove_authorization(git_repo: Path) -> None:
    assert init_artifact(git_repo).returncode == 0
    context = json.loads(context_path(git_repo).read_text(encoding="utf-8"))
    context["state"]["phase"] = "ARTIFACT_REMOVE"
    context_path(git_repo).write_text(
        json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    result = run_cli(
        git_repo,
        "remove",
        "--workflow-id",
        "demo-workflow",
        "--expected-revision",
        "0",
        "--authorize",
        "WRONG_GATE",
    )

    assert result.returncode != 0
    assert artifact_root(git_repo).exists()


def test_remove_deletes_exactly_one_owned_workflow_directory(git_repo: Path) -> None:
    assert init_artifact(git_repo, "demo-workflow").returncode == 0
    assert init_artifact(git_repo, "keep-workflow").returncode == 0
    context_path(git_repo, "demo-workflow").write_text(
        json.dumps(
            {
                **json.loads(
                    context_path(git_repo, "demo-workflow").read_text(encoding="utf-8")
                ),
                "state": {
                    "phase": "ARTIFACT_REMOVE",
                    "stopped_from": None,
                    "artifact_revision": 0,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    keep = artifact_root(git_repo, "keep-workflow")
    (keep / "user-note.txt").write_text("preserve\n", encoding="utf-8")

    result = run_cli(
        git_repo,
        "remove",
        "--workflow-id",
        "demo-workflow",
        "--expected-revision",
        "0",
        "--phase",
        "ARTIFACT_REMOVE",
        "--authorize",
        "ARTIFACT_REMOVE",
    )

    assert result.returncode == 0, result.stderr
    assert not artifact_root(git_repo, "demo-workflow").exists()
    assert keep.exists()
    assert (keep / "user-note.txt").read_text(encoding="utf-8") == "preserve\n"


def test_remove_rejects_symlinked_artifact(git_repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    workflows = git_repo / ".aidocs" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "demo-workflow").symlink_to(outside, target_is_directory=True)

    result = run_cli(
        git_repo,
        "remove",
        "--workflow-id",
        "demo-workflow",
        "--expected-revision",
        "0",
        "--phase",
        "ARTIFACT_REMOVE",
        "--authorize",
        "ARTIFACT_REMOVE",
    )

    assert result.returncode != 0
    assert (workflows / "demo-workflow").is_symlink()
    assert outside.exists()
