from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

import gitlab_review_sync as sync


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repo(tmp_path: Path, content: str = "one\ntwo\nthree\n") -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Review Test")
    git(repo, "config", "user.email", "review@example.com")
    (repo / "sample.txt").write_text(content)
    git(repo, "add", "sample.txt")
    git(repo, "commit", "-m", "initial")
    (repo / ".review").mkdir()
    return repo, git(repo, "rev-parse", "HEAD")


def make_entry(repo: Path, runner: sync.Runner) -> dict[str, Any]:
    head = git(repo, "rev-parse", "HEAD")
    return {
        "id": "entry-1",
        "relative_file": "sample.txt",
        "capture_head_sha": head,
        "capture_file_blob": git(repo, "hash-object", "--", "sample.txt"),
        "reviewed_text": "two",
        "start_line": 2,
        "end_line": 2,
        "category": "must",
        "comment": "Please fix this.",
        "gitlab": {
            "host": "git.example.test",
            "source_project_id": 10,
            "target_project_id": 20,
            "source_branch": "feature",
            "mr_iid": 3,
            "expected_head_sha": head,
        },
    }


def write_yaml(repo: Path, *entries: dict[str, Any]) -> Path:
    path = repo / ".review" / "review_comments.yaml"
    path.write_text(
        yaml.safe_dump({"reviews": list(entries)}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def reload_entry(yaml_path: Path, entry_id: str) -> dict[str, Any]:
    return sync.find_entry(
        sync.load_review_document(yaml_path, sync.Runner()), entry_id
    )


def version(head: str) -> dict[str, Any]:
    return {
        "id": 10,
        "state": "collected",
        "base_commit_sha": "base",
        "start_commit_sha": "start",
        "head_commit_sha": head,
    }


def sample_diff() -> dict[str, Any]:
    return {
        "old_path": "sample.txt",
        "new_path": "sample.txt",
        "diff": "@@ -1,3 +1,3 @@\n one\n-two\n+two\n three\n",
    }


class FakeClient:
    def __init__(
        self,
        head: str,
        *,
        version_diffs: list[Any] | None = None,
        inherit_reply_position: bool = False,
    ) -> None:
        self.host = "git.example.test"
        self.head = head
        self.version_diffs = [sample_diff()] if version_diffs is None else version_diffs
        self.inherit_reply_position = inherit_reply_position
        self.discussions: list[dict[str, Any]] = []
        self.calls: list[tuple[str, str, dict[str, Any] | None, bool]] = []
        self.user = {"id": 7, "username": "reviewer"}

    def api(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        self.calls.append((endpoint, method, payload, paginate))
        if endpoint == "user":
            return self.user
        if endpoint.endswith("/versions"):
            return [version(self.head)]
        if endpoint.endswith("/versions/10"):
            return {**version(self.head), "diffs": self.version_diffs}
        if "/diffs" in endpoint:
            raise AssertionError("Generic MR diffs endpoint is not supported")
        if endpoint.endswith("/discussions?per_page=100"):
            return self.discussions
        if "/discussions/" in endpoint and endpoint.endswith("/notes"):
            discussion_id = endpoint.split("/discussions/")[1].split("/")[0]
            discussion = self._discussion(discussion_id)
            position = (
                discussion["notes"][0].get("position")
                if self.inherit_reply_position
                else None
            )
            note = self._note(payload["body"], position=position, resolvable=False)
            discussion["notes"].append(note)
            return note
        if "/discussions/" in endpoint:
            discussion_id = endpoint.rsplit("/", 1)[-1]
            discussion = self._discussion(discussion_id)
            if method == "PUT":
                for note in discussion["notes"]:
                    if note.get("resolvable"):
                        note["resolved"] = bool(payload["resolved"])
            return discussion
        if endpoint.endswith("/discussions"):
            discussion = {
                "id": f"discussion-{len(self.discussions) + 1}",
                "individual_note": False,
                "notes": [
                    self._note(
                        payload["body"],
                        position=payload.get("position"),
                        resolvable=True,
                    )
                ],
            }
            self.discussions.append(discussion)
            return discussion
        if "/merge_requests/" in endpoint:
            return {
                "state": "opened",
                "sha": self.head,
                "source_project_id": 10,
                "target_project_id": 20,
                "source_branch": "feature",
                "iid": 3,
            }
        raise AssertionError(f"Unexpected API call: {method} {endpoint}")

    def _discussion(self, discussion_id: str) -> dict[str, Any]:
        return next(item for item in self.discussions if item["id"] == discussion_id)

    def _note(
        self,
        body: str,
        *,
        position: dict[str, Any] | None,
        resolvable: bool,
    ) -> dict[str, Any]:
        return {
            "id": sum(len(item["notes"]) for item in self.discussions) + 100,
            "body": body,
            "author": self.user,
            "position": position,
            "system": False,
            "resolvable": resolvable,
            "resolved": False,
        }


class RecordingRunner(sync.Runner):
    def __init__(self, output: str = "{}") -> None:
        self.output = output
        self.calls: list[tuple[list[str], Path, str | None]] = []

    def run(
        self,
        args: list[str],
        *,
        cwd: Path,
        input_text: str | None = None,
    ) -> str:
        self.calls.append((list(args), cwd, input_text))
        return self.output


def test_glab_write_uses_explicit_host_method_and_stdin_payload(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    client = sync.GlabClient("git.example.test", tmp_path, runner)
    payload = {"body": "Text with $() and `ticks`"}

    client.api(
        "projects/20/merge_requests/3/discussions",
        method="POST",
        payload=payload,
    )

    args, cwd, input_text = runner.calls[0]
    assert cwd == tmp_path
    assert args == [
        "glab",
        "api",
        "projects/20/merge_requests/3/discussions",
        "--hostname",
        "git.example.test",
        "--method",
        "POST",
        "--header",
        "Content-Type: application/json",
        "--input",
        "-",
    ]
    assert json.loads(input_text) == payload
    assert payload["body"] not in args


def test_runner_error_redacts_supported_token_forms(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = subprocess.CompletedProcess(
        args=["glab"],
        returncode=1,
        stdout="",
        stderr=(
            "glpat-secret PRIVATE-TOKEN: secret "
            "Authorization: Bearer bearer-secret api_token=api-secret"
        ),
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: result)

    with pytest.raises(sync.SyncError) as exc_info:
        sync.Runner().run(["glab", "api", "user"], cwd=tmp_path)

    message = str(exc_info.value)
    assert "glpat-secret" not in message
    assert "bearer-secret" not in message
    assert "api-secret" not in message
    assert " PRIVATE-TOKEN: secret" not in message


def test_parse_new_line_map_handles_context_and_added_lines() -> None:
    mapping = sync.parse_new_line_map(
        "@@ -10,4 +10,5 @@\n context\n-old\n+new\n+extra\n tail\n"
    )

    assert mapping == {10: 10, 11: None, 12: None, 13: 12}


def test_build_position_uses_both_paths_and_multiline_codes() -> None:
    diff = {
        "old_path": "old/name.txt",
        "new_path": "new/name.txt",
        "diff": "@@ -1,2 +1,3 @@\n one\n+inserted\n two\n",
    }

    position = sync.build_position(diff, version("head"), 1, 2)

    assert position["old_path"] == "old/name.txt"
    assert position["new_path"] == "new/name.txt"
    assert position["line_range"]["start"]["old_line"] == 1
    assert position["line_range"]["start"]["type"] == "old"
    assert position["line_range"]["end"]["type"] == "new"
    assert position["line_range"]["end"]["new_line"] == 2
    assert position["line_range"]["end"]["line_code"].endswith("_0_2")


def test_build_position_rejects_lines_outside_diff() -> None:
    with pytest.raises(sync.SyncError, match="not fully present"):
        sync.build_position(sample_diff(), version("head"), 2, 5)


def test_build_position_rejects_invalid_range() -> None:
    with pytest.raises(sync.SyncError, match="range is invalid"):
        sync.build_position(sample_diff(), version("head"), 3, 2)


def test_render_original_neutralizes_mentions_and_quick_actions() -> None:
    entry = {
        "id": "abc",
        "category": "q",
        "comment": "/close\nPlease ask @all",
    }

    body = sync.render_original(entry)

    assert body.startswith("[Q] ")
    # GitLab は描画後の text node から mention を拾い、quick action は raw body
    # から拾う。entity では前者を防げないので zero-width space で一致を壊す。
    assert "/close" not in body
    assert "@all" not in body
    assert "/\u200bclose" in body
    assert "@\u200ball" in body
    assert "&#" not in body


def test_render_original_keeps_markdown_and_adds_no_decoration() -> None:
    entry = {
        "id": "abc",
        "category": "q",
        "comment": "`%` は api/handler で使いますか？",
    }

    body = sync.render_original(entry)

    assert body == "[Q] `%` は api/handler で使いますか？"
    assert "<pre>" not in body
    assert "review-respond:" not in body


def test_render_reply_uses_the_plain_answer_header() -> None:
    body = sync.render_reply("answer", "はい。`%` は literal として扱います。")

    assert body == "[AIによる回答]\n\nはい。`%` は literal として扱います。"
    assert "<pre>" not in body
    assert "review-respond:" not in body


def test_neutralization_keeps_code_spans_and_fences_readable() -> None:
    body = sync.render_reply(
        "answer",
        "`@dataclass` を使います。\n\n```\n/close\n```",
    )

    # entity なら code span / fence 内で literal 表示されてしまう。
    assert "&#" not in body
    assert body.replace("\u200b", "").endswith(
        "`@dataclass` を使います。\n\n```\n/close\n```"
    )
    assert "@\u200bdataclass" in body
    assert "/\u200bclose" in body


@pytest.mark.parametrize(
    "comment",
    [
        "token: glpat-secret",
        "see /home/alice/private.txt",
        "see /tmp/run/output.log",
        "see `/root/private/output.log`",
        "see /etc",
        "see `/.env`",
        "see path:/home/alice/private.txt",
        "see [/home/alice/private.txt]",
        "see file:///home/alice/private.txt",
        "see /workspace",
        r"see C:\Users\alice\private.txt",
        r"see \\server\share\private.txt",
    ],
)
def test_render_original_rejects_sensitive_text(comment: str) -> None:
    with pytest.raises(sync.SyncError):
        sync.render_original({"id": "abc", "category": "must", "comment": comment})


def test_render_reply_rejects_absolute_path() -> None:
    with pytest.raises(sync.SyncError, match="absolute path"):
        sync.render_reply("resolution", "Tests: /workspace/run/output.log")


def test_render_original_rejects_invalid_category() -> None:
    with pytest.raises(sync.SyncError, match="category"):
        sync.render_original(
            {"id": "abc", "category": "@all", "comment": "Please review."}
        )


def test_render_reply_rejects_invalid_phase() -> None:
    with pytest.raises(sync.SyncError, match="phase identity"):
        sync.render_reply("resolution:bad -->", "Fixed.")


def test_validate_snapshot_requires_worktree_and_head_to_match_capture(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    entry = make_entry(repo, runner)
    sync.validate_snapshot(repo, entry, head, runner)

    (repo / "sample.txt").write_text("one\nchanged\nthree\n")

    with pytest.raises(sync.SyncError, match="not identical"):
        sync.validate_snapshot(repo, entry, head, runner)


def test_resolve_position_uses_selected_version_detail(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)

    _, selected_version, position = sync.resolve_position(
        repo,
        entry,
        client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        runner=runner,
    )

    assert selected_version["id"] == 10
    assert position["base_sha"] == selected_version["base_commit_sha"]
    assert position["start_sha"] == selected_version["start_commit_sha"]
    assert position["head_sha"] == selected_version["head_commit_sha"]
    assert "diffs" not in selected_version
    assert any(call[0].endswith("/versions/10") for call in client.calls)
    assert all("/diffs" not in call[0] for call in client.calls)


def test_resolve_position_selects_target_from_six_version_diffs(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    unrelated = [
        {
            **sample_diff(),
            "old_path": f"other-{index}.txt",
            "new_path": f"other-{index}.txt",
        }
        for index in range(5)
    ]
    client = FakeClient(head, version_diffs=[*unrelated, sample_diff()])
    entry = make_entry(repo, runner)

    _, _, position = sync.resolve_position(
        repo,
        entry,
        client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        runner=runner,
    )

    assert position["new_path"] == "sample.txt"
    assert all("/diffs" not in call[0] for call in client.calls)


@pytest.mark.parametrize(
    ("detail", "message"),
    [
        ({**version("different"), "diffs": [sample_diff()]}, "changed"),
        ({**version("head"), "diffs": [None]}, "malformed diff"),
    ],
)
def test_mr_version_detail_rejects_inconsistent_or_malformed_response(
    detail: dict[str, Any],
    message: str,
) -> None:
    class DetailClient:
        def api(self, endpoint: str) -> dict[str, Any]:
            assert endpoint.endswith("/versions/10")
            return detail

    with pytest.raises(sync.SyncError, match=message):
        sync._mr_version_detail(
            DetailClient(),
            target_project_id=20,
            mr_iid=3,
            version=version("head"),
        )


def test_post_original_is_idempotent_after_local_state_loss(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)

    created = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    reused = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )

    assert created["reused"] is False
    assert reused["reused"] is True
    assert len(client.discussions) == 1


def test_post_original_rejects_pinned_mr_identity_mismatch(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    entry["gitlab"]["mr_iid"] = 99

    with pytest.raises(sync.SyncError, match="Pinned GitLab identity"):
        sync.post_original(
            repo_root=repo,
            entry=entry,
            client=client,
            target_project_id=20,
            mr_iid=3,
            expected_head_sha=head,
            mode="inline",
            confirmed_legacy=False,
            runner=runner,
        )


def test_post_original_rejects_changed_content_after_post(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    posted = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = posted["discussion_id"]
    entry["gitlab"]["original_note_id"] = posted["note_id"]
    entry["comment"] = "A different comment must not create another discussion."

    with pytest.raises(sync.SyncError, match="different content"):
        sync.post_original(
            repo_root=repo,
            entry=entry,
            client=client,
            target_project_id=20,
            mr_iid=3,
            expected_head_sha=head,
            mode="inline",
            confirmed_legacy=False,
            runner=runner,
        )

    assert len(client.discussions) == 1


def test_post_original_rejects_identical_body_from_another_author(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    body = sync.render_original(entry)
    client.discussions.append(
        {
            "id": "copied",
            "individual_note": False,
            "notes": [
                {
                    "id": 1,
                    "body": body,
                    "author": {"id": 99},
                    "position": sync.build_position(sample_diff(), version(head), 2, 2),
                    "resolvable": True,
                    "resolved": False,
                }
            ],
        }
    )

    with pytest.raises(sync.SyncError, match="different author"):
        sync.post_original(
            repo_root=repo,
            entry=entry,
            client=client,
            target_project_id=20,
            mr_iid=3,
            expected_head_sha=head,
            mode="inline",
            confirmed_legacy=False,
            runner=runner,
        )


def test_reply_retry_and_unexpected_human_reply_block_resolve(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = original["discussion_id"]
    entry["gitlab"]["original_note_id"] = original["note_id"]

    first = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=entry,
        phase="resolution",
        text="Fixed and tested.",
        runner=runner,
    )
    second = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=entry,
        phase="resolution",
        text="Fixed and tested.",
        runner=runner,
    )
    assert first["reused"] is False
    assert second["reused"] is True

    client.discussions[0]["notes"].append(
        {
            "id": 500,
            "body": "Please also cover the edge case.",
            "author": {"id": 99},
            "position": None,
            "system": False,
            "resolvable": False,
            "resolved": False,
        }
    )
    with pytest.raises(sync.SyncError, match="unexpected human reply"):
        sync.resolve_discussion(
            repo_root=repo,
            client=client,
            target_project_id=20,
            mr_iid=3,
            discussion_id=original["discussion_id"],
            expected_head_sha=head,
            entry=entry,
        )


def test_reply_accepts_position_inherited_from_inline_discussion(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head, inherit_reply_position=True)
    entry = make_entry(repo, runner)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = original["discussion_id"]
    entry["gitlab"]["original_note_id"] = original["note_id"]

    first = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=entry,
        phase="resolution",
        text="Fixed and tested.",
        runner=runner,
    )
    second = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=entry,
        phase="resolution",
        text="Fixed and tested.",
        runner=runner,
    )

    assert first["position"] == original["position"]
    assert first["reused"] is False
    assert second["reused"] is True


def test_reply_accepts_verified_advanced_mr_head(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = original["discussion_id"]
    entry["gitlab"]["original_note_id"] = original["note_id"]

    (repo / "another.txt").write_text("published\n")
    git(repo, "add", "another.txt")
    git(repo, "commit", "-m", "publish fix")
    published_head = git(repo, "rev-parse", "HEAD")
    client.head = published_head
    entry["gitlab"]["expected_head_sha"] = published_head

    result = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=published_head,
        entry=entry,
        phase="resolution",
        text="Published and tested.",
        runner=runner,
    )

    assert result["reused"] is False


def test_reply_rejects_discussion_not_pinned_to_entry(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = "another-discussion"
    entry["gitlab"]["original_note_id"] = original["note_id"]

    with pytest.raises(sync.SyncError, match="pinned discussion"):
        sync.post_reply(
            repo_root=repo,
            client=client,
            target_project_id=20,
            mr_iid=3,
            discussion_id=original["discussion_id"],
            expected_head_sha=head,
            entry=entry,
            phase="resolution",
            text="Fixed.",
            runner=runner,
        )


def test_overview_mode_is_idempotent(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)

    first = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )
    second = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )

    assert first["position"] is None
    assert second["reused"] is True


def test_overview_discussion_accepts_the_ai_reply(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )
    entry["gitlab"]["discussion_id"] = original["discussion_id"]
    entry["gitlab"]["original_note_id"] = original["note_id"]

    reply = sync.post_reply(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=entry,
        phase="answer",
        text="はい、その理解で合っています。",
        runner=runner,
    )

    assert reply["discussion_id"] == original["discussion_id"]
    assert reply["reused"] is False
    notes = client.discussions[0]["notes"]
    assert len(notes) == 2
    assert notes[1]["body"].startswith("[AIによる回答]")


def test_post_original_persists_the_pin_and_blocks_edited_content(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    yaml_path = write_yaml(repo, entry)

    posted = sync.post_original(
        repo_root=repo,
        entry=entry,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )

    # POST と YAML 更新の間に窓を作らない（別コマンドの yaml-patch を待たない）。
    stored = reload_entry(yaml_path, "entry-1")["gitlab"]
    assert stored["discussion_id"] == posted["discussion_id"]
    assert stored["original_note_id"] == posted["note_id"]
    assert stored["mode"] == "inline"

    edited = reload_entry(yaml_path, "entry-1")
    edited["comment"] = "A different comment must not create another discussion."
    write_yaml(repo, edited)
    with pytest.raises(sync.SyncError, match="different content"):
        sync.post_original(
            repo_root=repo,
            entry=edited,
            yaml_path=yaml_path,
            client=client,
            target_project_id=20,
            mr_iid=3,
            expected_head_sha=head,
            mode="inline",
            confirmed_legacy=False,
            runner=runner,
        )
    assert len(client.discussions) == 1


def test_post_original_keeps_entries_with_identical_comments_apart(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    first = make_entry(repo, runner)
    second = {**make_entry(repo, runner), "id": "entry-2"}
    yaml_path = write_yaml(repo, first, second)

    posted_first = sync.post_original(
        repo_root=repo,
        entry=first,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )
    posted_second = sync.post_original(
        repo_root=repo,
        entry=second,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )

    assert posted_second["reused"] is False
    assert posted_second["discussion_id"] != posted_first["discussion_id"]
    assert len(client.discussions) == 2


def test_resolve_accepts_recorded_replies_and_rejects_a_same_author_human_reply(
    tmp_path: Path,
) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    yaml_path = write_yaml(repo, entry)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )
    sync.post_reply(
        repo_root=repo,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=reload_entry(yaml_path, "entry-1"),
        phase="answer",
        text="回答です。",
        runner=runner,
    )

    # 人間が同じアカウントから skill と同じ書式で返した reply を見逃さない。
    client.discussions[0]["notes"].append(
        {
            "id": 900,
            "body": "[Q] 本当にこの対応で良いですか？",
            "author": client.user,
            "position": None,
            "system": False,
            "resolvable": False,
            "resolved": False,
        }
    )
    with pytest.raises(sync.SyncError, match="unexpected human reply"):
        sync.resolve_discussion(
            repo_root=repo,
            client=client,
            target_project_id=20,
            mr_iid=3,
            discussion_id=original["discussion_id"],
            expected_head_sha=head,
            entry=reload_entry(yaml_path, "entry-1"),
            yaml_path=yaml_path,
            runner=runner,
        )

    client.discussions[0]["notes"] = [
        note for note in client.discussions[0]["notes"] if note["id"] != 900
    ]
    resolved = sync.resolve_discussion(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id=original["discussion_id"],
        expected_head_sha=head,
        entry=reload_entry(yaml_path, "entry-1"),
        yaml_path=yaml_path,
        runner=runner,
    )
    assert resolved["resolved"] is True


def test_reply_keeps_phases_apart_when_the_text_is_identical(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    yaml_path = write_yaml(repo, entry)
    original = sync.post_original(
        repo_root=repo,
        entry=entry,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="inline",
        confirmed_legacy=False,
        runner=runner,
    )

    def reply(phase: str) -> dict[str, Any]:
        return sync.post_reply(
            repo_root=repo,
            yaml_path=yaml_path,
            client=client,
            target_project_id=20,
            mr_iid=3,
            discussion_id=original["discussion_id"],
            expected_head_sha=head,
            entry=reload_entry(yaml_path, "entry-1"),
            phase=phase,
            text="同じ本文。",
            runner=runner,
        )

    answer = reply("answer")
    resolution = reply("resolution")
    retried = reply("resolution")

    assert answer["note_id"] != resolution["note_id"]
    assert resolution["reused"] is False
    assert retried["reused"] is True
    assert retried["note_id"] == resolution["note_id"]
    replies = reload_entry(yaml_path, "entry-1")["gitlab"]["replies"]
    assert replies == {"answer": answer["note_id"], "resolution": resolution["note_id"]}


def test_legacy_marker_thread_still_accepts_reply_and_resolve(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    runner = sync.Runner()
    client = FakeClient(head)
    entry = make_entry(repo, runner)
    legacy_body = (
        "**Local review [must]**\n\n<pre>Please fix this.</pre>\n\n"
        "<!-- review-respond:entry-1:original:0123456789abcdef0123 -->"
    )
    client.discussions.append(
        {
            "id": "legacy-discussion",
            "individual_note": False,
            "notes": [
                {
                    "id": 42,
                    "body": legacy_body,
                    "author": client.user,
                    "position": None,
                    "system": False,
                    "resolvable": True,
                    "resolved": False,
                }
            ],
        }
    )
    entry["gitlab"]["discussion_id"] = "legacy-discussion"
    entry["gitlab"]["original_note_id"] = 42
    yaml_path = write_yaml(repo, entry)

    reused = sync.post_original(
        repo_root=repo,
        entry=entry,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        expected_head_sha=head,
        mode="overview",
        confirmed_legacy=False,
        runner=runner,
    )
    assert reused["reused"] is True
    assert len(client.discussions) == 1

    sync.post_reply(
        repo_root=repo,
        yaml_path=yaml_path,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id="legacy-discussion",
        expected_head_sha=head,
        entry=reload_entry(yaml_path, "entry-1"),
        phase="answer",
        text="新書式で返信します。",
        runner=runner,
    )
    resolved = sync.resolve_discussion(
        repo_root=repo,
        client=client,
        target_project_id=20,
        mr_iid=3,
        discussion_id="legacy-discussion",
        expected_head_sha=head,
        entry=reload_entry(yaml_path, "entry-1"),
        yaml_path=yaml_path,
        runner=runner,
    )
    assert resolved["resolved"] is True


def test_yaml_patch_is_atomic_and_preserves_other_entries(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"
    yaml_path.write_text(
        "reviews:\n"
        "  - id: first\n"
        "    status: pending\n"
        "  - id: second\n"
        "    status: pending\n"
    )

    updated = sync.yaml_patch(
        yaml_path,
        "first",
        {"status": "awaiting_publish", "gitlab": {"mr_iid": 7}},
        sync.Runner(),
    )
    document = sync.load_review_document(yaml_path, sync.Runner())

    assert updated["status"] == "awaiting_publish"
    assert document["reviews"][0]["gitlab"]["mr_iid"] == 7
    assert document["reviews"][1]["status"] == "pending"
    assert not (review_dir / ".lock").exists()


def test_yaml_patch_rejects_non_object_patch(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"
    yaml_path.write_text("reviews:\n  - id: first\n    status: pending\n")

    with pytest.raises(sync.SyncError, match="JSON object"):
        sync.yaml_patch(yaml_path, "first", ["invalid"], sync.Runner())


def test_yaml_patch_cli_reads_free_form_patch_from_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"
    yaml_path.write_text("reviews:\n  - id: first\n    status: pending\n")
    patch_path = tmp_path / "patch.json"
    patch_path.write_text(
        json.dumps(
            {
                "status": "awaiting_publish",
                "resolution": "Handles quotes, $(), and `ticks` without shell parsing.",
            }
        )
    )

    exit_code = sync.main(
        [
            "yaml-patch",
            "--yaml",
            str(yaml_path),
            "--entry-id",
            "first",
            "--patch-file",
            str(patch_path),
        ]
    )
    document = sync.load_review_document(yaml_path, sync.Runner())

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "awaiting_publish"
    assert document["reviews"][0]["resolution"].startswith("Handles quotes")


def test_migrate_legacy_entry_adds_stable_id_atomically(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"
    yaml_path.write_text(
        "reviews:\n"
        "  - file: sample.txt\n"
        "    comment: Legacy review\n"
        "    status: pending\n"
    )

    first = sync.migrate_legacy_entry(yaml_path, 1, sync.Runner())
    second = sync.migrate_legacy_entry(yaml_path, 1, sync.Runner())
    document = sync.load_review_document(yaml_path, sync.Runner())

    assert first["id"].startswith("legacy-")
    assert second["id"] == first["id"]
    assert document["reviews"][0]["id"] == first["id"]
    assert not (review_dir / ".lock").exists()


def test_archive_requires_all_entries_to_be_resolved(tmp_path: Path) -> None:
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    yaml_path = review_dir / "review_comments.yaml"
    yaml_path.write_text("reviews:\n  - id: first\n    status: pending\n")

    with pytest.raises(sync.SyncError, match="non-resolved"):
        sync.archive_review(yaml_path, sync.Runner())

    sync.yaml_patch(
        yaml_path,
        "first",
        {"status": "resolved"},
        sync.Runner(),
    )
    destination = sync.archive_review(yaml_path, sync.Runner())

    assert destination.parent == review_dir / "archive"
    assert destination.exists()
    assert not yaml_path.exists()


class DiscoverRunner(sync.Runner):
    def __init__(
        self,
        *,
        branch_push_remote: str = "",
        push_default: str = "",
        branch_remote: str = "origin",
        remote_urls: str = "git@git.example.test:group/source.git\n",
    ) -> None:
        self.calls: list[list[str]] = []
        self.branch_push_remote = branch_push_remote
        self.push_default = push_default
        self.branch_remote = branch_remote
        self.remote_urls = remote_urls

    def run(
        self,
        args: list[str],
        *,
        cwd: Path,
        input_text: str | None = None,
    ) -> str:
        self.calls.append(list(args))
        if args[:4] == ["git", "-C", str(cwd), "symbolic-ref"]:
            return "feature\n"
        if args[:4] == ["git", "-C", str(cwd), "config"]:
            key = args[-1]
            if key == "branch.feature.pushRemote":
                return self.branch_push_remote + (
                    "\n" if self.branch_push_remote else ""
                )
            if key == "remote.pushDefault":
                return self.push_default + ("\n" if self.push_default else "")
            if key == "branch.feature.remote":
                return self.branch_remote + ("\n" if self.branch_remote else "")
            raise AssertionError(args)
        if args[:4] == ["git", "-C", str(cwd), "remote"]:
            return self.remote_urls
        if args[:4] == ["git", "-C", str(cwd), "rev-parse"]:
            return "head\n"
        if args[:3] == [
            "glab",
            "api",
            "projects/group%2Fsource",
        ]:
            return json.dumps({"id": 10, "path_with_namespace": "group/source"})
        if args[:2] == ["glab", "api"] and args[2].startswith("merge_requests?"):
            return "\n".join(
                [
                    json.dumps(
                        {
                            "source_project_id": 10,
                            "target_project_id": 20,
                            "source_branch": "feature",
                            "target_branch": "main",
                            "iid": 3,
                            "title": "Right",
                            "web_url": "https://git.example.test/mr/3",
                            "sha": "head",
                        }
                    ),
                    json.dumps(
                        {
                            "source_project_id": 99,
                            "target_project_id": 20,
                            "source_branch": "feature",
                            "target_branch": "main",
                            "iid": 4,
                            "title": "Wrong project",
                            "web_url": "https://git.example.test/mr/4",
                            "sha": "other",
                        }
                    ),
                ]
            )
        raise AssertionError(args)


def test_discover_filters_by_source_project_and_fixes_cli_boundary(
    tmp_path: Path,
) -> None:
    runner = DiscoverRunner()

    result = sync.discover(tmp_path, runner)

    assert [candidate["iid"] for candidate in result["candidates"]] == [3]
    mr_call = next(
        call
        for call in runner.calls
        if call[1:2] == ["api"] and call[2].startswith("merge_requests?")
    )
    assert "scope=all" in mr_call[2]
    assert "state=opened" in mr_call[2]
    assert ["--hostname", "git.example.test"] == mr_call[3:5]
    assert "--paginate" in mr_call
    assert "--output" in mr_call


def test_discover_uses_git_push_remote_precedence(tmp_path: Path) -> None:
    runner = DiscoverRunner(
        branch_push_remote="fork",
        push_default="default",
        branch_remote="upstream",
    )

    result = sync.discover(tmp_path, runner)

    assert result["push_remote"] == "fork"
    remote_call = next(call for call in runner.calls if call[3:4] == ["remote"])
    assert remote_call[-1] == "fork"
    assert "--all" in remote_call


def test_discover_rejects_multiple_push_urls(tmp_path: Path) -> None:
    runner = DiscoverRunner(
        remote_urls=(
            "git@git.example.test:group/source.git\n"
            "git@git.example.test:group/mirror.git\n"
        )
    )

    with pytest.raises(sync.SyncError, match="exactly one"):
        sync.discover(tmp_path, runner)
