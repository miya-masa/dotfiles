from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


REVIEW_LUA = Path(__file__).parents[2] / "dot_config/nvim/lua/plugins/review.lua"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    file_path = repo / "sample.txt"
    file_path.write_text("one\ntwo\nthree\n")
    git(repo, "init")
    git(repo, "config", "user.name", "Review Test")
    git(repo, "config", "user.email", "review@example.com")
    git(repo, "add", "sample.txt")
    git(repo, "commit", "-m", "initial")
    return repo, file_path


def run_nvim(tmp_path: Path, lua: str) -> subprocess.CompletedProcess[str]:
    script = tmp_path / "capture.lua"
    script.write_text(lua)
    return subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-l", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_capture_records_content_identity_for_saved_dirty_file(
    tmp_path: Path,
) -> None:
    repo, file_path = make_repo(tmp_path)
    capture_head = git(repo, "rev-parse", "HEAD")
    file_path.write_text("one\nchanged\nthree\n")
    expected_blob = git(repo, "hash-object", "--", "sample.txt")
    result = run_nvim(
        tmp_path,
        f"""
local spec = dofile({str(REVIEW_LUA)!r})
vim.cmd("edit " .. vim.fn.fnameescape({str(file_path)!r}))
vim.api.nvim_win_set_cursor(0, {{ 2, 0 }})
local range, err = spec._review.get_range_normal()
assert(range, err)
spec._review.save_yaml(range, "Please review this.", "must")
vim.cmd("qa!")
""",
    )
    assert result.returncode == 0, result.stderr

    document = yaml.safe_load((repo / ".review/review_comments.yaml").read_text())
    entry = document["reviews"][0]
    assert entry["id"]
    assert entry["relative_file"] == "sample.txt"
    assert entry["capture_head_sha"] == capture_head
    assert entry["capture_file_blob"] == expected_blob
    assert entry["reviewed_text"] == "changed"
    assert entry["context_before"] == ["one"]
    assert entry["context_after"] == ["three"]


def test_capture_rejects_unsaved_buffer(tmp_path: Path) -> None:
    _, file_path = make_repo(tmp_path)
    result = run_nvim(
        tmp_path,
        f"""
local spec = dofile({str(REVIEW_LUA)!r})
vim.cmd("edit " .. vim.fn.fnameescape({str(file_path)!r}))
vim.api.nvim_buf_set_lines(0, 0, 1, false, {{ "unsaved" }})
local range, err = spec._review.get_range_normal()
assert(range == nil)
assert(err:match("Save the file"))
vim.cmd("qa!")
""",
    )

    assert result.returncode == 0, result.stderr
