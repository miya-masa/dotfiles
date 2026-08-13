#!/usr/bin/env python3
"""Safe GitLab discussion primitives for the review-respond skill."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import quote, urlencode, urlparse


class SyncError(RuntimeError):
    """An expected, user-actionable synchronization error."""


_HUNK_RE = re.compile(
    r"^@@ -(?P<old>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new>\d+)(?:,(?P<new_count>\d+))? @@"
)
_LOCAL_PATH_RE = re.compile(
    r"(?:"
    r"file:///[^\s\"'<>]+|"
    r"/(?:home|Users|root|tmp|workspace)(?:[/\\]|(?=[\s\"'`)\]}>.,;:]|$))|"
    r"(?<![:/A-Za-z0-9])/(?!/)[^/\s\"'<>]+(?:/[^\s\"'<>]*)?|"
    r"[A-Za-z]:[\\/][^\s\"'<>]+|"
    r"\\\\[^\\\s\"'<>]+\\[^\s\"'<>]+)"
)
_SAFE_NO_ARGUMENT_QUICK_ACTION_RE = re.compile(
    r"(?m)^/(?:approve|close|done|lock|merge|reopen|subscribe|todo|"
    r"unapprove|unlock|unsubscribe)\s*$"
)
_CREDENTIAL_RE = re.compile(
    r"(?:glpat-[A-Za-z0-9_-]+|PRIVATE-TOKEN|Authorization\s*:\s*Bearer|"
    r"(?:access|api|private)[_-]?token\s*[:=])",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    text = re.sub(r"glpat-[A-Za-z0-9_-]+", "glpat-[REDACTED]", text)
    text = re.sub(
        r"((?:Authorization\s*:\s*Bearer|PRIVATE-TOKEN\s*:))\s*\S+",
        r"\1 [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"((?:access|api|private)[_-]?token\s*[:=])\s*\S+",
        r"\1[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    return text


class Runner:
    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        input_text: str | None = None,
    ) -> str:
        proc = subprocess.run(
            list(args),
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            command = " ".join(args[:3])
            detail = _redact(proc.stderr.strip() or proc.stdout.strip())
            raise SyncError(f"{command} failed: {detail or f'exit {proc.returncode}'}")
        return proc.stdout


def _git(runner: Runner, repo_root: Path, *args: str) -> str:
    return runner.run(["git", "-C", str(repo_root), *args], cwd=repo_root).strip()


def _git_optional(runner: Runner, repo_root: Path, *args: str) -> str:
    try:
        return _git(runner, repo_root, *args)
    except SyncError as exc:
        if str(exc).endswith("exit 1"):
            return ""
        raise


def _remote_identity(remote_url: str) -> tuple[str, str]:
    if "://" in remote_url:
        parsed = urlparse(remote_url)
        host = parsed.hostname
        path = parsed.path.lstrip("/")
    else:
        match = re.match(r"^(?:[^@]+@)?([^:]+):(.+)$", remote_url)
        if not match:
            raise SyncError("Git remote URL is not a supported GitLab URL")
        host, path = match.groups()
    if not host or not path:
        raise SyncError("Failed to resolve GitLab host and project from the remote")
    return host, path.removesuffix(".git")


class GlabClient:
    def __init__(self, host: str, repo_root: Path, runner: Runner) -> None:
        self.host = host
        self.repo_root = repo_root
        self.runner = runner

    def api(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        args = ["glab", "api", endpoint, "--hostname", self.host, "--method", method]
        input_text = None
        if paginate:
            args.extend(["--paginate", "--output", "ndjson"])
        if payload is not None:
            args.extend(["--header", "Content-Type: application/json", "--input", "-"])
            input_text = json.dumps(payload, ensure_ascii=False)
        output = self.runner.run(args, cwd=self.repo_root, input_text=input_text)
        if paginate:
            return [json.loads(line) for line in output.splitlines() if line.strip()]
        if not output.strip():
            return None
        return json.loads(output)


def discover(repo_root: Path, runner: Runner) -> dict[str, Any]:
    branch = _git(runner, repo_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        raise SyncError("Detached HEAD is not supported")

    remote = (
        _git_optional(
            runner,
            repo_root,
            "config",
            "--get",
            f"branch.{branch}.pushRemote",
        )
        or _git_optional(runner, repo_root, "config", "--get", "remote.pushDefault")
        or _git_optional(
            runner,
            repo_root,
            "config",
            "--get",
            f"branch.{branch}.remote",
        )
        or "origin"
    )
    if remote == ".":
        raise SyncError("A local-only branch remote cannot identify a GitLab project")

    remote_urls = {
        line
        for line in _git(
            runner,
            repo_root,
            "remote",
            "get-url",
            "--push",
            "--all",
            remote,
        ).splitlines()
        if line
    }
    if len(remote_urls) != 1:
        raise SyncError("Push remote must resolve to exactly one GitLab URL")
    remote_url = remote_urls.pop()
    host, project_path = _remote_identity(remote_url)
    client = GlabClient(host, repo_root, runner)
    source_project = client.api(f"projects/{quote(project_path, safe='')}")

    query = urlencode(
        {
            "scope": "all",
            "state": "opened",
            "source_branch": branch,
            "per_page": 100,
        }
    )
    candidates = client.api(f"merge_requests?{query}", paginate=True)
    candidates = [
        mr
        for mr in candidates
        if mr.get("source_project_id") == source_project.get("id")
        and mr.get("source_branch") == branch
    ]

    return {
        "host": host,
        "push_remote": remote,
        "source_project_id": source_project["id"],
        "source_project_path": source_project["path_with_namespace"],
        "source_branch": branch,
        "local_head_sha": _git(runner, repo_root, "rev-parse", "HEAD"),
        "candidates": [
            {
                "target_project_id": mr["target_project_id"],
                "source_project_id": mr["source_project_id"],
                "iid": mr["iid"],
                "title": mr["title"],
                "web_url": mr["web_url"],
                "sha": mr["sha"],
                "target_branch": mr["target_branch"],
            }
            for mr in candidates
        ],
    }


def load_review_document(yaml_path: Path, runner: Runner) -> dict[str, Any]:
    output = runner.run(
        ["yq", "-o=json", ".", str(yaml_path)],
        cwd=yaml_path.parent,
    )
    document = json.loads(output)
    if not isinstance(document, dict) or not isinstance(document.get("reviews"), list):
        raise SyncError("Review YAML must contain a reviews list")
    return document


def find_entry(document: dict[str, Any], entry_id: str) -> dict[str, Any]:
    matches = [entry for entry in document["reviews"] if entry.get("id") == entry_id]
    if len(matches) != 1:
        raise SyncError(f"Expected exactly one review entry for id {entry_id}")
    return matches[0]


@contextlib.contextmanager
def review_lock(review_dir: Path) -> Iterator[None]:
    lock_dir = review_dir / ".lock"
    try:
        lock_dir.mkdir()
    except FileExistsError as exc:
        raise SyncError(
            f"Review data is busy; inspect a possibly stale lock at {lock_dir}"
        ) from exc
    try:
        yield
    finally:
        try:
            lock_dir.rmdir()
        except OSError:
            pass


def yaml_patch(
    yaml_path: Path,
    entry_id: str,
    patch: dict[str, Any],
    runner: Runner,
) -> dict[str, Any]:
    if not isinstance(patch, dict):
        raise SyncError("YAML patch must be a JSON object")
    with review_lock(yaml_path.parent):
        document = load_review_document(yaml_path, runner)
        entry = find_entry(document, entry_id)
        _deep_merge(entry, patch)
        _write_review_document(yaml_path, document, runner)
    return find_entry(document, entry_id)


def migrate_legacy_entry(
    yaml_path: Path,
    entry_index: int,
    runner: Runner,
) -> dict[str, Any]:
    with review_lock(yaml_path.parent):
        document = load_review_document(yaml_path, runner)
        if entry_index < 1 or entry_index > len(document["reviews"]):
            raise SyncError("Legacy entry index is outside the reviews list")
        entry = document["reviews"][entry_index - 1]
        if entry.get("id"):
            return entry
        canonical = json.dumps(
            {"index": entry_index, "entry": entry},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        entry_id = (
            "legacy-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
        )
        if any(item.get("id") == entry_id for item in document["reviews"]):
            raise SyncError("Generated legacy review ID conflicts with another entry")
        entry["id"] = entry_id
        _write_review_document(yaml_path, document, runner)
        return entry


def _write_review_document(
    yaml_path: Path,
    document: dict[str, Any],
    runner: Runner,
) -> None:
    # yq renders a string containing tabs as a literal block scalar, and a
    # content line starting with a tab then fails re-parsing ("found a tab
    # character where an indentation space is expected"). Captured source is
    # tab-indented, so emit with PyYAML instead, which keeps those strings
    # double-quoted with escapes exactly as the capture writer does.
    import yaml as _yaml

    rendered = _yaml.safe_dump(
        document,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=10**9,
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=yaml_path.parent,
        prefix=f".{yaml_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(rendered)
        tmp_path = Path(tmp.name)
    try:
        runner.run(
            ["yq", "-e", ".", str(tmp_path)],
            cwd=yaml_path.parent,
        )
        os.replace(tmp_path, yaml_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def archive_review(yaml_path: Path, runner: Runner) -> Path:
    with review_lock(yaml_path.parent):
        document = load_review_document(yaml_path, runner)
        incomplete = [
            entry.get("id") or entry.get("file")
            for entry in document["reviews"]
            if entry.get("status", "pending") != "resolved"
        ]
        if incomplete:
            raise SyncError("Review YAML still contains non-resolved entries")
        archive_dir = yaml_path.parent / "archive"
        archive_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S")
        destination = archive_dir / f"{timestamp}.yaml"
        if destination.exists():
            raise SyncError(f"Archive destination already exists: {destination}")
        os.replace(yaml_path, destination)
    return destination


def _deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def parse_new_line_map(diff_text: str) -> dict[int, int | None]:
    mapping: dict[int, int | None] = {}
    old_line: int | None = None
    new_line: int | None = None
    in_hunk = False

    for line in diff_text.splitlines():
        hunk = _HUNK_RE.match(line)
        if hunk:
            old_line = int(hunk.group("old"))
            new_line = int(hunk.group("new"))
            in_hunk = True
            continue
        if not in_hunk or old_line is None or new_line is None:
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            mapping[new_line] = None
            new_line += 1
        elif line.startswith("-"):
            old_line += 1
        else:
            mapping[new_line] = old_line
            old_line += 1
            new_line += 1
    return mapping


def _line_code(path: str, old_line: int | None, new_line: int) -> str:
    path_hash = hashlib.sha1(path.encode("utf-8")).hexdigest()
    return f"{path_hash}_{old_line or 0}_{new_line}"


def build_position(
    diff: dict[str, Any],
    version: dict[str, Any],
    start_line: int,
    end_line: int,
) -> dict[str, Any]:
    if start_line < 1 or end_line < start_line:
        raise SyncError("Review line range is invalid")
    mapping = parse_new_line_map(diff.get("diff", ""))
    missing = [line for line in range(start_line, end_line + 1) if line not in mapping]
    if missing:
        raise SyncError(
            f"Selected line range is not fully present in the MR diff: {missing[0]}"
        )

    position: dict[str, Any] = {
        "position_type": "text",
        "base_sha": version["base_commit_sha"],
        "start_sha": version["start_commit_sha"],
        "head_sha": version["head_commit_sha"],
        "old_path": diff["old_path"],
        "new_path": diff["new_path"],
    }
    if start_line == end_line:
        position["new_line"] = start_line
        if mapping[start_line] is not None:
            position["old_line"] = mapping[start_line]
        return position

    def endpoint(line: int) -> dict[str, Any]:
        old = mapping[line]
        result: dict[str, Any] = {
            "line_code": _line_code(diff["new_path"], old, line),
            "type": "new" if old is None else "old",
            "new_line": line,
        }
        if old is not None:
            result["old_line"] = old
        return result

    position["new_line"] = end_line
    if mapping[end_line] is not None:
        position["old_line"] = mapping[end_line]
    position["line_range"] = {
        "start": endpoint(start_line),
        "end": endpoint(end_line),
    }
    return position


def _mr_context(
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    mr = client.api(f"projects/{target_project_id}/merge_requests/{mr_iid}")
    if mr.get("state") != "opened":
        raise SyncError("Pinned merge request is not open")
    versions = client.api(
        f"projects/{target_project_id}/merge_requests/{mr_iid}/versions"
    )
    if not versions:
        raise SyncError("Merge request has no collected diff version")
    version = versions[0]
    if version.get("state") != "collected":
        raise SyncError("Latest merge request diff version is not collected")
    if version.get("head_commit_sha") != mr.get("sha"):
        raise SyncError("Merge request head and latest diff version disagree")
    return mr, version


def _mr_version_detail(
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
    version: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    version_id = version.get("id")
    if version_id is None:
        raise SyncError("Selected merge request diff version has no ID")
    detail = client.api(
        f"projects/{target_project_id}/merge_requests/{mr_iid}/versions/{version_id}"
    )
    if not isinstance(detail, dict):
        raise SyncError("Merge request diff version detail is not an object")
    identity_keys = (
        "id",
        "state",
        "base_commit_sha",
        "start_commit_sha",
        "head_commit_sha",
    )
    if any(
        version.get(key) is None or detail.get(key) != version.get(key)
        for key in identity_keys
    ):
        raise SyncError("Merge request diff version detail changed during preflight")
    diffs = detail.get("diffs")
    if not isinstance(diffs, list):
        raise SyncError("Merge request diff version has no diffs list")
    if not all(isinstance(diff, dict) for diff in diffs):
        raise SyncError("Merge request diff version contains a malformed diff")
    return detail, diffs


def _head_blob(runner: Runner, repo_root: Path, relative_file: str) -> str:
    result = _git(runner, repo_root, "ls-tree", "HEAD", "--", relative_file)
    if not result or "\t" not in result:
        raise SyncError(f"File is not present at local HEAD: {relative_file}")
    metadata, path = result.split("\t", 1)
    if path != relative_file:
        raise SyncError("Git returned an unexpected path for the captured file")
    fields = metadata.split()
    if len(fields) != 3 or fields[1] != "blob":
        raise SyncError("Captured path is not a Git blob at HEAD")
    return fields[2]


def validate_snapshot(
    repo_root: Path,
    entry: dict[str, Any],
    mr_head_sha: str,
    runner: Runner,
) -> None:
    required = {
        "relative_file",
        "capture_head_sha",
        "capture_file_blob",
        "reviewed_text",
        "start_line",
        "end_line",
    }
    missing = sorted(required - entry.keys())
    if missing:
        raise SyncError(
            "Legacy review entry lacks synchronization metadata: " + ", ".join(missing)
        )

    local_head = _git(runner, repo_root, "rev-parse", "HEAD")
    if local_head != mr_head_sha:
        raise SyncError("Local HEAD is not the pinned merge request HEAD")

    relative_file = entry["relative_file"]
    path = (repo_root / relative_file).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise SyncError("Review file escapes the worktree") from exc

    working_blob = _git(runner, repo_root, "hash-object", "--", relative_file)
    head_blob = _head_blob(runner, repo_root, relative_file)
    capture_blob = entry["capture_file_blob"]
    if working_blob != capture_blob or head_blob != capture_blob:
        raise SyncError(
            "Captured file content is not identical to the working tree and MR HEAD"
        )

    lines = path.read_text(encoding="utf-8").splitlines()
    start = int(entry["start_line"])
    end = int(entry["end_line"])
    if start < 1 or end < start or end > len(lines):
        raise SyncError("Captured review line range is invalid")
    reviewed_text = "\n".join(lines[start - 1 : end])
    if reviewed_text != entry["reviewed_text"]:
        raise SyncError("Captured review text no longer matches its line range")


def resolve_position(
    repo_root: Path,
    entry: dict[str, Any],
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
    expected_head_sha: str,
    runner: Runner,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    mr, version = _mr_context(client, target_project_id, mr_iid)
    validate_pinned_identity(
        entry,
        client=client,
        mr=mr,
        target_project_id=target_project_id,
        mr_iid=mr_iid,
        expected_head_sha=expected_head_sha,
    )
    if mr["sha"] != expected_head_sha:
        raise SyncError("Merge request HEAD changed; rerun preflight")
    validate_snapshot(repo_root, entry, mr["sha"], runner)

    version_detail, version_diffs = _mr_version_detail(
        client,
        target_project_id,
        mr_iid,
        version,
    )
    relative_file = entry["relative_file"]
    diffs = [diff for diff in version_diffs if diff.get("new_path") == relative_file]
    if len(diffs) != 1:
        raise SyncError(
            f"Expected exactly one MR diff for {relative_file}, found {len(diffs)}"
        )
    if not all(
        isinstance(diffs[0].get(key), str) for key in ("old_path", "new_path", "diff")
    ):
        raise SyncError("Selected merge request diff is malformed")
    position = build_position(
        diffs[0],
        version_detail,
        int(entry["start_line"]),
        int(entry["end_line"]),
    )
    return mr, version, position


def validate_pinned_identity(
    entry: dict[str, Any],
    *,
    client: GlabClient,
    mr: dict[str, Any],
    target_project_id: int,
    mr_iid: int,
    expected_head_sha: str,
) -> None:
    pinned = entry.get("gitlab")
    if not isinstance(pinned, dict):
        raise SyncError("Review entry has no pinned GitLab identity")
    expected = {
        "host": client.host,
        "target_project_id": target_project_id,
        "mr_iid": mr_iid,
        "expected_head_sha": expected_head_sha,
        "source_project_id": mr.get("source_project_id"),
        "source_branch": mr.get("source_branch"),
    }
    mismatches = [
        key
        for key, value in expected.items()
        if value is None or pinned.get(key) != value
    ]
    if mismatches:
        raise SyncError(
            "Pinned GitLab identity does not match the requested MR: "
            + ", ".join(mismatches)
        )


def _safe_fragment(text: str) -> str:
    if _CREDENTIAL_RE.search(text):
        raise SyncError("Outbound review text appears to contain a credential")
    path_probe = _SAFE_NO_ARGUMENT_QUICK_ACTION_RE.sub("", text)
    if _LOCAL_PATH_RE.search(path_probe):
        raise SyncError("Outbound review text contains a local absolute path")
    escaped = html.escape(text, quote=False)
    return escaped.replace("@", "&#64;").replace("/", "&#47;")


def operation_marker(entry_id: str, phase: str, text: str) -> str:
    marker_component = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    if not marker_component.fullmatch(entry_id) or not marker_component.fullmatch(
        phase
    ):
        raise SyncError("Review marker identity is invalid")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
    return f"<!-- review-respond:{entry_id}:{phase}:{digest} -->"


def render_original(entry: dict[str, Any]) -> tuple[str, str]:
    category = entry.get("category") or ("imo" if "severity" in entry else "imo")
    if category not in {"must", "imo", "q"}:
        raise SyncError("Review category must be must, imo, or q")
    comment = str(entry.get("comment", "")).rstrip()
    if not comment:
        raise SyncError("Review comment is empty")
    marker = operation_marker(entry["id"], "original", comment)
    body = (
        f"**Local review [{category}]**\n\n"
        f"<pre>{_safe_fragment(comment)}</pre>\n\n"
        f"{marker}"
    )
    return body, marker


def render_reply(entry_id: str, phase: str, text: str) -> tuple[str, str]:
    text = text.rstrip()
    if not text:
        raise SyncError("Reply text is empty")
    marker = operation_marker(entry_id, phase, text)
    body = f"**AI review response**\n\n<pre>{_safe_fragment(text)}</pre>\n\n{marker}"
    return body, marker


def _discussions(
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
) -> list[dict[str, Any]]:
    return client.api(
        f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions?per_page=100",
        paginate=True,
    )


def _current_user(client: GlabClient) -> dict[str, Any]:
    return client.api("user")


def _find_marker(
    discussions: list[dict[str, Any]],
    marker: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for discussion in discussions:
        for note in discussion.get("notes", []):
            if marker in (note.get("body") or ""):
                matches.append((discussion, note))
    return matches


def _find_marker_prefix(
    discussions: list[dict[str, Any]],
    marker_prefix: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for discussion in discussions:
        for note in discussion.get("notes", []):
            if marker_prefix in (note.get("body") or ""):
                matches.append((discussion, note))
    return matches


def _reject_conflicting_phase(
    discussions: list[dict[str, Any]],
    *,
    entry_id: str,
    phase: str,
    exact_marker: str,
) -> None:
    prefix = f"<!-- review-respond:{entry_id}:{phase}:"
    matches = _find_marker_prefix(discussions, prefix)
    if any(exact_marker not in (note.get("body") or "") for _, note in matches):
        raise SyncError(f"GitLab already contains different content for phase {phase}")


def _validate_owned_note(
    discussion: dict[str, Any],
    note: dict[str, Any],
    *,
    body: str,
    user_id: int,
    position: dict[str, Any] | None,
    allow_missing_position: bool = False,
) -> None:
    if note.get("body") != body or note.get("author", {}).get("id") != user_id:
        raise SyncError("Existing idempotency marker belongs to a different note")
    if position is None:
        if note.get("position") is not None:
            raise SyncError("Existing overview note unexpectedly has a diff position")
        return
    actual_position = note.get("position")
    if actual_position is None and allow_missing_position:
        pass
    elif not _contains_mapping(actual_position, position):
        raise SyncError("Existing note position differs from the captured position")
    if discussion.get("individual_note"):
        raise SyncError("Existing marker is not in a resolvable discussion")


def _contains_mapping(actual: Any, expected: Any) -> bool:
    if not isinstance(expected, dict):
        return actual == expected
    if not isinstance(actual, dict):
        return False
    return all(
        key in actual and _contains_mapping(actual[key], value)
        for key, value in expected.items()
    )


def _validate_pinned_discussion(
    entry: dict[str, Any],
    *,
    discussion_id: str,
    discussion: dict[str, Any],
    body: str,
    marker: str,
    user_id: int,
) -> dict[str, Any]:
    pinned = entry.get("gitlab")
    if not isinstance(pinned, dict) or pinned.get("discussion_id") != discussion_id:
        raise SyncError(
            "Discussion does not match the review entry's pinned discussion"
        )
    matches = _find_marker([discussion], marker)
    if len(matches) != 1:
        raise SyncError("Pinned discussion does not contain the original review note")
    matched_discussion, note = matches[0]
    if pinned.get("original_note_id") != note.get("id"):
        raise SyncError("Discussion does not contain the pinned original note")
    _validate_owned_note(
        matched_discussion,
        note,
        body=body,
        user_id=user_id,
        position=note.get("position"),
    )
    return note


def post_original(
    *,
    repo_root: Path,
    entry: dict[str, Any],
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
    expected_head_sha: str,
    mode: str,
    confirmed_legacy: bool,
    runner: Runner,
) -> dict[str, Any]:
    body, marker = render_original(entry)
    with review_lock(repo_root / ".review"):
        mr, _ = _mr_context(client, target_project_id, mr_iid)
        validate_pinned_identity(
            entry,
            client=client,
            mr=mr,
            target_project_id=target_project_id,
            mr_iid=mr_iid,
            expected_head_sha=expected_head_sha,
        )
        if mr["sha"] != expected_head_sha:
            raise SyncError("Merge request HEAD changed before posting")

        position = None
        if mode == "inline":
            _, _, position = resolve_position(
                repo_root,
                entry,
                client,
                target_project_id,
                mr_iid,
                expected_head_sha,
                runner,
            )
        elif not confirmed_legacy:
            validate_snapshot(repo_root, entry, mr["sha"], runner)

        user = _current_user(client)
        discussions = _discussions(client, target_project_id, mr_iid)
        _reject_conflicting_phase(
            discussions,
            entry_id=entry["id"],
            phase="original",
            exact_marker=marker,
        )
        matches = _find_marker(discussions, marker)
        if len(matches) > 1:
            raise SyncError("Multiple GitLab notes contain the same idempotency marker")
        if matches:
            discussion, note = matches[0]
            _validate_owned_note(
                discussion,
                note,
                body=body,
                user_id=user["id"],
                position=position,
            )
            return _operation_result(discussion, note, reused=True)

        payload: dict[str, Any] = {"body": body}
        if position is not None:
            payload["position"] = position
        created = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions",
            method="POST",
            payload=payload,
        )
        fetched = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{created['id']}"
        )
        matches = _find_marker([fetched], marker)
        if len(matches) != 1:
            raise SyncError("Created discussion could not be verified")
        discussion, note = matches[0]
        _validate_owned_note(
            discussion,
            note,
            body=body,
            user_id=user["id"],
            position=position,
        )
        return _operation_result(discussion, note, reused=False)


def post_reply(
    *,
    repo_root: Path,
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
    discussion_id: str,
    expected_head_sha: str,
    entry: dict[str, Any],
    phase: str,
    text: str,
) -> dict[str, Any]:
    entry_id = entry["id"]
    body, marker = render_reply(entry_id, phase, text)
    original_body, original_marker = render_original(entry)
    with review_lock(repo_root / ".review"):
        mr, _ = _mr_context(client, target_project_id, mr_iid)
        validate_pinned_identity(
            entry,
            client=client,
            mr=mr,
            target_project_id=target_project_id,
            mr_iid=mr_iid,
            expected_head_sha=expected_head_sha,
        )
        if mr["sha"] != expected_head_sha:
            raise SyncError("Merge request HEAD changed before replying")
        user = _current_user(client)
        discussion = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}"
        )
        original_note = _validate_pinned_discussion(
            entry,
            discussion_id=discussion_id,
            discussion=discussion,
            body=original_body,
            marker=original_marker,
            user_id=user["id"],
        )
        _reject_conflicting_phase(
            [discussion],
            entry_id=entry_id,
            phase=phase,
            exact_marker=marker,
        )
        matches = _find_marker([discussion], marker)
        if len(matches) > 1:
            raise SyncError("Multiple replies contain the same idempotency marker")
        if matches:
            _, note = matches[0]
            _validate_owned_note(
                discussion,
                note,
                body=body,
                user_id=user["id"],
                position=original_note.get("position"),
                allow_missing_position=True,
            )
            return _operation_result(discussion, note, reused=True)

        note = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}/notes",
            method="POST",
            payload={"body": body},
        )
        fetched = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}"
        )
        matches = _find_marker([fetched], marker)
        if len(matches) != 1:
            raise SyncError("Created reply could not be verified")
        _, verified_note = matches[0]
        _validate_owned_note(
            fetched,
            verified_note,
            body=body,
            user_id=user["id"],
            position=original_note.get("position"),
            allow_missing_position=True,
        )
        return _operation_result(fetched, verified_note, reused=False)


def resolve_discussion(
    *,
    repo_root: Path,
    client: GlabClient,
    target_project_id: int,
    mr_iid: int,
    discussion_id: str,
    expected_head_sha: str,
    entry: dict[str, Any],
) -> dict[str, Any]:
    entry_id = entry["id"]
    original_body, original_marker = render_original(entry)
    with review_lock(repo_root / ".review"):
        mr, _ = _mr_context(client, target_project_id, mr_iid)
        validate_pinned_identity(
            entry,
            client=client,
            mr=mr,
            target_project_id=target_project_id,
            mr_iid=mr_iid,
            expected_head_sha=expected_head_sha,
        )
        if mr["sha"] != expected_head_sha:
            raise SyncError("Merge request HEAD changed before resolving")
        user = _current_user(client)
        discussion = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}"
        )
        _validate_pinned_discussion(
            entry,
            discussion_id=discussion_id,
            discussion=discussion,
            body=original_body,
            marker=original_marker,
            user_id=user["id"],
        )
        marker_prefix = f"<!-- review-respond:{entry_id}:"
        for note in discussion.get("notes", []):
            if note.get("system"):
                continue
            if note.get("author", {}).get("id") != user["id"] or marker_prefix not in (
                note.get("body") or ""
            ):
                raise SyncError(
                    "Discussion has an unexpected human reply; manual decision is required"
                )
        resolvable = [
            note for note in discussion.get("notes", []) if note.get("resolvable")
        ]
        if not resolvable:
            raise SyncError("Discussion is not resolvable")
        if all(note.get("resolved") for note in resolvable):
            return {"discussion_id": discussion_id, "resolved": True, "reused": True}

        client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}",
            method="PUT",
            payload={"resolved": True},
        )
        fetched = client.api(
            f"projects/{target_project_id}/merge_requests/{mr_iid}/discussions/{discussion_id}"
        )
        fetched_resolvable = [
            note for note in fetched.get("notes", []) if note.get("resolvable")
        ]
        if not fetched_resolvable or not all(
            note.get("resolved") for note in fetched_resolvable
        ):
            raise SyncError("Discussion resolve operation could not be verified")
        return {"discussion_id": discussion_id, "resolved": True, "reused": False}


def _operation_result(
    discussion: dict[str, Any],
    note: dict[str, Any],
    *,
    reused: bool,
) -> dict[str, Any]:
    return {
        "discussion_id": discussion["id"],
        "note_id": note["id"],
        "position": note.get("position"),
        "reused": reused,
    }


def _entry_from_args(args: argparse.Namespace, runner: Runner) -> dict[str, Any]:
    document = load_review_document(Path(args.yaml).resolve(), runner)
    return find_entry(document, args.entry_id)


def _client_from_args(args: argparse.Namespace, runner: Runner) -> GlabClient:
    return GlabClient(args.host, Path(args.repo_root).resolve(), runner)


def _add_pinned_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--target-project-id", required=True, type=int)
    parser.add_argument("--mr-iid", required=True, type=int)
    parser.add_argument("--expected-head-sha", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("--repo-root", required=True)

    position_parser = subparsers.add_parser("position")
    _add_pinned_arguments(position_parser)
    position_parser.add_argument("--yaml", required=True)
    position_parser.add_argument("--entry-id", required=True)

    original_parser = subparsers.add_parser("post-original")
    _add_pinned_arguments(original_parser)
    original_parser.add_argument("--yaml", required=True)
    original_parser.add_argument("--entry-id", required=True)
    original_parser.add_argument(
        "--mode",
        choices=("inline", "overview"),
        default="inline",
    )
    original_parser.add_argument("--confirmed-legacy", action="store_true")

    reply_parser = subparsers.add_parser("reply")
    _add_pinned_arguments(reply_parser)
    reply_parser.add_argument("--yaml", required=True)
    reply_parser.add_argument("--discussion-id", required=True)
    reply_parser.add_argument("--entry-id", required=True)
    reply_parser.add_argument("--phase", required=True)
    reply_parser.add_argument("--body-file", required=True)

    resolve_parser = subparsers.add_parser("resolve")
    _add_pinned_arguments(resolve_parser)
    resolve_parser.add_argument("--yaml", required=True)
    resolve_parser.add_argument("--discussion-id", required=True)
    resolve_parser.add_argument("--entry-id", required=True)

    patch_parser = subparsers.add_parser("yaml-patch")
    patch_parser.add_argument("--yaml", required=True)
    patch_parser.add_argument("--entry-id", required=True)
    patch_group = patch_parser.add_mutually_exclusive_group(required=True)
    patch_group.add_argument("--patch-json")
    patch_group.add_argument("--patch-file")

    migrate_parser = subparsers.add_parser("migrate-legacy")
    migrate_parser.add_argument("--yaml", required=True)
    migrate_parser.add_argument("--entry-index", required=True, type=int)

    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("--yaml", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = Runner()
    try:
        if args.command == "discover":
            result = discover(Path(args.repo_root).resolve(), runner)
        elif args.command == "yaml-patch":
            patch_text = (
                Path(args.patch_file).read_text(encoding="utf-8")
                if args.patch_file
                else args.patch_json
            )
            result = yaml_patch(
                Path(args.yaml).resolve(),
                args.entry_id,
                json.loads(patch_text),
                runner,
            )
        elif args.command == "migrate-legacy":
            result = migrate_legacy_entry(
                Path(args.yaml).resolve(),
                args.entry_index,
                runner,
            )
        elif args.command == "archive":
            result = {
                "archive_path": str(archive_review(Path(args.yaml).resolve(), runner))
            }
        else:
            repo_root = Path(args.repo_root).resolve()
            client = _client_from_args(args, runner)
            if args.command == "position":
                entry = _entry_from_args(args, runner)
                mr, version, position = resolve_position(
                    repo_root,
                    entry,
                    client,
                    args.target_project_id,
                    args.mr_iid,
                    args.expected_head_sha,
                    runner,
                )
                result = {"mr": mr, "version": version, "position": position}
            elif args.command == "post-original":
                result = post_original(
                    repo_root=repo_root,
                    entry=_entry_from_args(args, runner),
                    client=client,
                    target_project_id=args.target_project_id,
                    mr_iid=args.mr_iid,
                    expected_head_sha=args.expected_head_sha,
                    mode=args.mode,
                    confirmed_legacy=args.confirmed_legacy,
                    runner=runner,
                )
            elif args.command == "reply":
                text = Path(args.body_file).read_text(encoding="utf-8")
                entry = _entry_from_args(args, runner)
                result = post_reply(
                    repo_root=repo_root,
                    client=client,
                    target_project_id=args.target_project_id,
                    mr_iid=args.mr_iid,
                    discussion_id=args.discussion_id,
                    expected_head_sha=args.expected_head_sha,
                    entry=entry,
                    phase=args.phase,
                    text=text,
                )
            elif args.command == "resolve":
                entry = _entry_from_args(args, runner)
                result = resolve_discussion(
                    repo_root=repo_root,
                    client=client,
                    target_project_id=args.target_project_id,
                    mr_iid=args.mr_iid,
                    discussion_id=args.discussion_id,
                    expected_head_sha=args.expected_head_sha,
                    entry=entry,
                )
            else:
                raise AssertionError(f"Unhandled command: {args.command}")
    except (OSError, ValueError, json.JSONDecodeError, SyncError) as exc:
        print(f"error: {_redact(str(exc))}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
