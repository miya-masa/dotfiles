from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "dot_agents/workflows/software_delivery/scripts/review_snapshot.py"


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
    assert run_git(tmp_path, "init", "-q", "-b", "main").returncode == 0
    (tmp_path / "tracked.txt").write_text("base\n", encoding="utf-8")
    (tmp_path / "mode.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (tmp_path / "external.txt").write_text("external\n", encoding="utf-8")
    assert (
        run_git(tmp_path, "add", "tracked.txt", "mode.sh", "external.txt").returncode
        == 0
    )
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


def base_commit(repo: Path) -> str:
    result = run_git(repo, "rev-parse", "HEAD")
    assert result.returncode == 0
    return result.stdout.strip()


def allowlist(*paths: str) -> str:
    return json.dumps({"version": 1, "paths": list(paths)})


def run_cli(
    repo: Path,
    paths: tuple[str, ...],
    *extra: str,
    source: str = "worktree",
    output: Path | None = None,
    base: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    manifest_path = output or repo / "manifest.json"
    args = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(repo),
        "--base-commit",
        base or base_commit(repo),
        "--allowlist-json",
        allowlist(*paths),
        "--source",
        source,
        "--output",
        str(manifest_path),
        *extra,
    ]
    return (
        subprocess.run(args, cwd=repo, text=True, capture_output=True, check=False),
        manifest_path,
    )


def result_json(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.stdout.strip(), result.stderr
    return json.loads(result.stdout)


def snapshot_id(result: subprocess.CompletedProcess[str]) -> str:
    return result_json(result)["review_snapshot_id"]


def index_stat_signature(path: Path) -> tuple[int, int, int, int, int, int, int]:
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def test_manifest_contains_canonical_allowed_states_and_git_blob_hashes(
    git_repo: Path,
) -> None:
    tracked = git_repo / "tracked.txt"
    tracked.write_text("changed\n", encoding="utf-8")
    untracked = git_repo / "new.txt"
    untracked.write_bytes(b"new\x00content")
    (git_repo / "external.txt").unlink()
    mode = git_repo / "mode.sh"
    mode.chmod(0o755)
    link = git_repo / "link"
    link.symlink_to("tracked.txt")

    result, manifest_path = run_cli(
        git_repo,
        ("tracked.txt", "new.txt", "external.txt", "mode.sh", "link", "gone.txt"),
    )
    assert result.returncode == 0, result.stderr
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert document == {
        "base_commit": base_commit(git_repo),
        "paths": [
            {
                "content_sha256": hashlib.sha256(b"external\n").hexdigest(),
                "mode": "100644",
                "path": "external.txt",
                "state": "deleted",
            },
            {
                "content_sha256": None,
                "mode": None,
                "path": "gone.txt",
                "state": "absent",
            },
            {
                "content_sha256": hashlib.sha256(b"tracked.txt").hexdigest(),
                "mode": "120000",
                "path": "link",
                "state": "present",
            },
            {
                "content_sha256": hashlib.sha256(b"#!/bin/sh\nexit 0\n").hexdigest(),
                "mode": "100755",
                "path": "mode.sh",
                "state": "present",
            },
            {
                "content_sha256": hashlib.sha256(b"new\x00content").hexdigest(),
                "mode": "100644",
                "path": "new.txt",
                "state": "present",
            },
            {
                "content_sha256": hashlib.sha256(b"changed\n").hexdigest(),
                "mode": "100644",
                "path": "tracked.txt",
                "state": "present",
            },
        ],
    }
    assert snapshot_id(result).startswith("sha256:")
    assert result_json(result)["preflight"]["external_dirty_paths"] == []


def test_base_content_mode_and_deletion_changes_change_id(git_repo: Path) -> None:
    base = base_commit(git_repo)
    clean, _ = run_cli(git_repo, ("tracked.txt",), base=base)
    assert clean.returncode == 0

    (git_repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    changed, _ = run_cli(git_repo, ("tracked.txt",), base=base)
    assert changed.returncode == 0
    assert snapshot_id(changed) != snapshot_id(clean)

    (git_repo / "tracked.txt").unlink()
    deleted, _ = run_cli(git_repo, ("tracked.txt",), base=base)
    assert deleted.returncode == 0
    assert snapshot_id(deleted) != snapshot_id(changed)

    (git_repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    (git_repo / "tracked.txt").chmod(0o755)
    mode, _ = run_cli(git_repo, ("tracked.txt",), base=base)
    assert mode.returncode == 0
    assert snapshot_id(mode) != snapshot_id(clean)

    assert run_git(git_repo, "add", "tracked.txt").returncode == 0
    assert (
        run_git(
            git_repo,
            "-c",
            "user.name=Codex Test",
            "-c",
            "user.email=codex@example.invalid",
            "commit",
            "-qm",
            "second",
        ).returncode
        == 0
    )
    second_base, _ = run_cli(git_repo, ("tracked.txt",), base=base_commit(git_repo))
    assert second_base.returncode == 0
    assert snapshot_id(second_base) != snapshot_id(clean)


def test_worktree_and_index_equal_intended_trees_have_equal_ids(git_repo: Path) -> None:
    target = git_repo / "tracked.txt"
    target.write_text("same final tree\n", encoding="utf-8")
    (git_repo / "mode.sh").chmod(0o755)
    (git_repo / "added-link").symlink_to("tracked.txt")
    worktree, _ = run_cli(
        git_repo,
        ("tracked.txt", "mode.sh", "added-link"),
        source="worktree",
    )
    assert worktree.returncode == 0, worktree.stderr

    assert (
        run_git(git_repo, "add", "tracked.txt", "mode.sh", "added-link").returncode == 0
    )
    index, _ = run_cli(
        git_repo,
        ("tracked.txt", "mode.sh", "added-link"),
        source="index",
    )
    assert index.returncode == 0, index.stderr
    assert snapshot_id(index) == snapshot_id(worktree)


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 2, "paths": ["tracked.txt"]},
        {"version": 1, "paths": ["tracked.txt", "tracked.txt"]},
        {"version": 1, "paths": ["../tracked.txt"]},
        {"version": 1, "paths": ["/absolute"]},
        {"version": 1, "paths": [".git/HEAD"]},
        {"version": 1, "paths": [".git"]},
        {"version": 1, "paths": ["tracked.txt/"]},
    ],
)
def test_invalid_allowlist_is_rejected_without_output_mutation(
    git_repo: Path, payload: dict
) -> None:
    output = git_repo / "manifest.json"
    output.write_bytes(b"old\n")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(git_repo),
            "--base-commit",
            base_commit(git_repo),
            "--allowlist-json",
            json.dumps(payload),
            "--source",
            "worktree",
            "--output",
            str(output),
        ],
        cwd=git_repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert output.read_bytes() == b"old\n"


def test_external_dirty_path_is_reported_and_excluded_from_id(git_repo: Path) -> None:
    allowed, _ = run_cli(git_repo, ("tracked.txt",))
    assert allowed.returncode == 0
    first_id = snapshot_id(allowed)

    (git_repo / "external.txt").write_text("user change\n", encoding="utf-8")
    dirty, _ = run_cli(git_repo, ("tracked.txt",))
    assert dirty.returncode == 0, dirty.stderr
    preflight = result_json(dirty)["preflight"]
    assert preflight["external_dirty_paths"] == ["external.txt"]
    assert preflight["external_staged_paths"] == []
    assert preflight["shipping_blocked"] is True
    assert snapshot_id(dirty) == first_id


def test_index_external_staged_path_fails_without_mutating_index(
    git_repo: Path,
) -> None:
    (git_repo / "external.txt").write_text("staged user change\n", encoding="utf-8")
    assert run_git(git_repo, "add", "external.txt").returncode == 0
    before = run_git(git_repo, "diff", "--cached", "--binary").stdout

    result, output = run_cli(
        git_repo,
        ("tracked.txt",),
        source="index",
    )
    assert result.returncode != 0
    assert "external.txt" in result.stderr
    assert not output.exists()
    assert run_git(git_repo, "diff", "--cached", "--binary").stdout == before


def test_snapshot_does_not_refresh_or_lock_the_index(git_repo: Path) -> None:
    index = git_repo / ".git" / "index"
    lock = git_repo / ".git" / "index.lock"
    before_bytes = index.read_bytes()
    before_stat = index_stat_signature(index)
    assert not lock.exists()

    target = git_repo / "tracked.txt"
    target_stat = target.stat()
    os.utime(
        target,
        ns=(target_stat.st_atime_ns, target_stat.st_mtime_ns + 10_000_000_000),
    )
    result, _ = run_cli(git_repo, ("tracked.txt",))
    assert result.returncode == 0, result.stderr

    assert index.read_bytes() == before_bytes
    assert index_stat_signature(index) == before_stat
    assert not lock.exists()


def test_output_write_is_atomic_and_stdout_is_structured_only(git_repo: Path) -> None:
    result, output = run_cli(git_repo, ("tracked.txt",))
    assert result.returncode == 0, result.stderr
    assert set(result_json(result)) == {"review_snapshot_id", "preflight"}
    assert output.is_file()
    assert not list(git_repo.glob(".manifest.json.*.tmp"))


def test_full_base_commit_is_required(git_repo: Path) -> None:
    short = base_commit(git_repo)[:8]
    result, _ = run_cli(git_repo, ("tracked.txt",), base=short)
    assert result.returncode != 0


def test_public_functions_are_importable(git_repo: Path) -> None:
    spec = importlib.util.spec_from_file_location("review_snapshot", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.snapshot(
        git_repo, base_commit(git_repo), ["tracked.txt"], "worktree"
    ).review_snapshot_id.startswith("sha256:")
