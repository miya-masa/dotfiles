from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / ".chezmoiscripts/run_once_after_remove_codex_context_guard.sh"
LEGACY_GUARD_FIXTURE = (
    Path(__file__).with_name("fixtures") / "legacy_codex_context_guard.bytes"
)
TARGET_RELATIVE_PATH = Path(".local/bin/codex-context-guard")


def legacy_guard_bytes() -> bytes:
    return LEGACY_GUARD_FIXTURE.read_bytes()


def migration_legacy_sha256() -> str:
    match = re.search(
        r'^readonly LEGACY_SHA256="([0-9a-f]{64})"$',
        MIGRATION.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    assert match is not None
    return match.group(1)


def run_migration(
    home: Path, *, path: str | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        ["/bin/bash", str(MIGRATION)],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_missing_guard_is_a_successful_no_op(tmp_path: Path) -> None:
    result = run_migration(tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_exact_legacy_guard_is_removed(tmp_path: Path) -> None:
    legacy_bytes = legacy_guard_bytes()
    assert hashlib.sha256(legacy_bytes).hexdigest() == migration_legacy_sha256()

    target = tmp_path / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(legacy_bytes)

    result = run_migration(tmp_path)

    assert result.returncode == 0, result.stderr
    assert not target.exists()
    assert result.stderr == ""


def test_modified_guard_is_preserved_with_warning(tmp_path: Path) -> None:
    modified_bytes = legacy_guard_bytes() + b"\n# user modification\n"
    target = tmp_path / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(modified_bytes)

    result = run_migration(tmp_path)

    assert result.returncode == 0, result.stderr
    assert target.exists()
    assert target.read_bytes() == modified_bytes
    assert "WARNING" in result.stderr
    assert str(target) in result.stderr


def test_symlink_guard_is_preserved_with_warning(tmp_path: Path) -> None:
    target = tmp_path / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.symlink_to("user-managed-guard")

    result = run_migration(tmp_path)

    assert result.returncode == 0, result.stderr
    assert target.is_symlink()
    assert "WARNING" in result.stderr
    assert str(target) in result.stderr


def test_directory_guard_is_preserved_with_warning(tmp_path: Path) -> None:
    target = tmp_path / TARGET_RELATIVE_PATH
    target.mkdir(parents=True)

    result = run_migration(tmp_path)

    assert result.returncode == 0, result.stderr
    assert target.is_dir()
    assert "WARNING" in result.stderr
    assert str(target) in result.stderr


def test_uses_shasum_when_sha256sum_is_unavailable(tmp_path: Path) -> None:
    legacy_bytes = legacy_guard_bytes()
    target = tmp_path / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(legacy_bytes)
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "rm").symlink_to("/bin/rm")
    (command_dir / "shasum").write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-a" ] && [ "$2" = "256" ]; then\n'
        f'  printf "%s  %s\\n" "{migration_legacy_sha256()}" "$3"\n'
        "fi\n",
        encoding="utf-8",
    )
    (command_dir / "shasum").chmod(0o755)

    result = run_migration(tmp_path, path=str(command_dir))

    assert result.returncode == 0, result.stderr
    assert not target.exists()
    assert result.stderr == ""


def test_preserves_guard_when_no_sha256_command_is_available(tmp_path: Path) -> None:
    target = tmp_path / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(legacy_guard_bytes())
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "rm").symlink_to("/bin/rm")

    result = run_migration(tmp_path, path=str(command_dir))

    assert result.returncode != 0
    assert target.exists()
    assert "ERROR" in result.stderr
    assert "sha256sum" in result.stderr
    assert "shasum" in result.stderr
