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


def save_comment(tmp_path: Path, file_path: Path, line: int, comment: str) -> None:
    result = run_nvim(
        tmp_path,
        f"""
local spec = dofile({str(REVIEW_LUA)!r})
vim.cmd("edit " .. vim.fn.fnameescape({str(file_path)!r}))
vim.api.nvim_win_set_cursor(0, {{ {line}, 0 }})
local range, err = spec._review.get_range_normal()
assert(range, err)
spec._review.save_yaml(range, {comment!r}, "must")
vim.cmd("qa!")
""",
    )
    assert result.returncode == 0, result.stderr


def test_append_survives_helper_rewrite(tmp_path: Path) -> None:
    """review-respond の helper は PyYAML の safe_dump で書き戻すので、リスト
    項目が column 0 に来る。固定インデントで連結追記するとここで壊れる。"""
    repo, file_path = make_repo(tmp_path)
    yaml_path = repo / ".review/review_comments.yaml"

    save_comment(tmp_path, file_path, 2, "first")
    document = yaml.safe_load(yaml_path.read_text())
    document["reviews"][0]["status"] = "resolved"
    yaml_path.write_text(
        yaml.safe_dump(
            document,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=10**9,
        )
    )
    assert yaml_path.read_text().splitlines()[1].startswith("- ")

    save_comment(tmp_path, file_path, 3, "second")

    reviews = yaml.safe_load(yaml_path.read_text())["reviews"]
    assert [entry["status"] for entry in reviews] == ["resolved", "pending"]
    assert reviews[1]["comment"].strip() == "second"


def test_append_to_emptied_and_unterminated_documents(tmp_path: Path) -> None:
    repo, file_path = make_repo(tmp_path)
    review_dir = repo / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"

    yaml_path.write_text("reviews: []\n")
    save_comment(tmp_path, file_path, 2, "after archive")
    assert len(yaml.safe_load(yaml_path.read_text())["reviews"]) == 1

    yaml_path.write_text('reviews:\n  - id: "x"\n    category: must\n    status: pending')
    save_comment(tmp_path, file_path, 2, "after hand edit")
    assert len(yaml.safe_load(yaml_path.read_text())["reviews"]) == 2


def test_carriage_returns_in_comment_do_not_break_the_document(tmp_path: Path) -> None:
    repo, file_path = make_repo(tmp_path)
    save_comment(tmp_path, file_path, 2, "line1\rline2\r\nline3")

    entry = yaml.safe_load((repo / ".review/review_comments.yaml").read_text())["reviews"][0]
    assert entry["comment"].strip().splitlines() == ["line1", "line2", "line3"]


def test_scalar_types_are_preserved(tmp_path: Path) -> None:
    """style を scalar まで広げると "123" の引用符が外れて int になる。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    file_path = repo / "sample.txt"
    file_path.write_text("123\ntrue\nnull\n")
    git(repo, "init")
    git(repo, "config", "user.name", "Review Test")
    git(repo, "config", "user.email", "review@example.com")
    git(repo, "add", "sample.txt")
    git(repo, "commit", "-m", "initial")

    save_comment(tmp_path, file_path, 1, "numeric looking line")

    entry = yaml.safe_load((repo / ".review/review_comments.yaml").read_text())["reviews"][0]
    assert entry["reviewed_text"] == "123"
    assert entry["context_after"] == ["true", "null"]
    assert entry["start_line"] == 1
