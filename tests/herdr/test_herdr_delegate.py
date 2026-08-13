from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "dot_local/bin/executable_herdr-delegate"


def make_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def run_helper(
    *args: str,
    input: str | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        input=input,
        text=True,
        capture_output=True,
        env=env,
        cwd=None if cwd is None else str(cwd),
        check=False,
    )


# ---------------------------------------------------------------------------
# build-prompt (AC1)
# ---------------------------------------------------------------------------


class BuildPromptTests(unittest.TestCase):
    def test_preserves_shell_metacharacters_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instruction = tmp_path / "instruction.md"
            tricky = (
                'レビューしてください `backtick` $(rm -rf /) と "quoted text" を含む'
            )
            instruction.write_text(tricky, encoding="utf-8")

            result = run_helper(
                "build-prompt",
                "--instruction-file",
                str(instruction),
                "--input-dir",
                str(tmp_path / "input"),
                "--output-path",
                str(tmp_path / "out" / "review.md"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(tricky, result.stdout)
            # No shell expansion happened: literal $(...) survives, and no
            # stray "rf" file listing / command output leaked into stdout.
            self.assertIn("$(rm -rf /)", result.stdout)


# ---------------------------------------------------------------------------
# parse-pane (AC2)
# ---------------------------------------------------------------------------


class ParsePaneTests(unittest.TestCase):
    def test_extracts_pane_id_from_valid_json(self) -> None:
        payload = json.dumps({"result": {"pane": {"pane_id": "wD:p9"}}})
        result = run_helper("parse-pane", input=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "wD:p9")

    def test_rejects_invalid_json(self) -> None:
        result = run_helper("parse-pane", input="{not json")
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_missing_pane_id(self) -> None:
        result = run_helper("parse-pane", input=json.dumps({"result": {"pane": {}}}))
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_missing_pane_object(self) -> None:
        result = run_helper("parse-pane", input=json.dumps({"result": {}}))
        self.assertNotEqual(result.returncode, 0)


# ---------------------------------------------------------------------------
# check-marker (AC3)
# ---------------------------------------------------------------------------


class CheckMarkerTests(unittest.TestCase):
    MARKER = "<!-- DELEGATE-COMPLETE -->"

    def test_missing_file_is_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_helper(
                "check-marker",
                "--path",
                str(Path(tmp) / "absent.md"),
                "--marker",
                self.MARKER,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_missing_marker_is_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            path.write_text("結果本文のみ、マーカー無し\n", encoding="utf-8")
            result = run_helper(
                "check-marker", "--path", str(path), "--marker", self.MARKER
            )
            self.assertNotEqual(result.returncode, 0)

    def test_marker_not_at_tail_is_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            path.write_text(f"{self.MARKER}\n本文がまだ続く\n", encoding="utf-8")
            result = run_helper(
                "check-marker", "--path", str(path), "--marker", self.MARKER
            )
            self.assertNotEqual(result.returncode, 0)

    def test_marker_at_tail_is_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            path.write_text(f"レビュー結果本文\n{self.MARKER}\n", encoding="utf-8")
            result = run_helper(
                "check-marker", "--path", str(path), "--marker", self.MARKER
            )
            self.assertEqual(result.returncode, 0, result.stderr)


# ---------------------------------------------------------------------------
# select-orphans (AC4, AC5)
# ---------------------------------------------------------------------------


class SelectOrphansTests(unittest.TestCase):
    def _write_records(self, path: Path, delegations: list[dict]) -> None:
        path.write_text(
            json.dumps(
                {"version": 1, "next_generation": 99, "delegations": delegations}
            ),
            encoding="utf-8",
        )

    def _agent_list(self, names: list[str]) -> str:
        return json.dumps({"result": {"agents": [{"name": name} for name in names]}})

    def test_excludes_held_wrong_mode_and_future_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "delegations.json"
            self._write_records(
                records,
                [
                    {
                        "generation": 1,
                        "role": "review",
                        "agent_name": "hd-aaaaaaaa-review-1",
                        "pane_id": "wD:p1",
                        "mode": "agent",
                        "state": "active",
                    },
                    {
                        # held -> excluded even though otherwise eligible.
                        "generation": 1,
                        "role": "review",
                        "agent_name": "hd-aaaaaaaa-review-2",
                        "pane_id": "wD:p2",
                        "mode": "agent",
                        "state": "held",
                    },
                    {
                        # mode is not "agent" -> excluded.
                        "generation": 1,
                        "role": "monitor",
                        "agent_name": "hd-aaaaaaaa-monitor-1",
                        "pane_id": "wD:p3",
                        "mode": "command:resident",
                        "state": "active",
                    },
                    {
                        # generation >= current -> excluded.
                        "generation": 3,
                        "role": "review",
                        "agent_name": "hd-aaaaaaaa-review-3",
                        "pane_id": "wD:p4",
                        "mode": "agent",
                        "state": "active",
                    },
                ],
            )
            agent_list = self._agent_list(
                [
                    "hd-aaaaaaaa-review-1",
                    "hd-aaaaaaaa-review-2",
                    "hd-aaaaaaaa-monitor-1",
                    "hd-aaaaaaaa-review-3",
                ]
            )
            result = run_helper(
                "select-orphans",
                "--agent-list-json",
                "-",
                "--records",
                str(records),
                "--current-generation",
                "3",
                input=agent_list,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), ["hd-aaaaaaaa-review-1"])

    def test_missing_records_file_is_no_orphans(self) -> None:
        """F3-a: no delegations.json yet (first-ever delegation in this
        workflow) is treated as "nothing to reclaim", not an error."""
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "delegations.json"  # deliberately never created
            agent_list = self._agent_list([])
            result = run_helper(
                "select-orphans",
                "--agent-list-json",
                "-",
                "--records",
                str(records),
                "--current-generation",
                "1",
                input=agent_list,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_records_file_present_but_invalid_json_is_nonzero(self) -> None:
        """F3-b: distinguishes "file absent" (F3-a, exit 0) from "file
        present but malformed" (must stay an error)."""
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "delegations.json"
            records.write_text("{not json", encoding="utf-8")
            agent_list = self._agent_list([])
            result = run_helper(
                "select-orphans",
                "--agent-list-json",
                "-",
                "--records",
                str(records),
                "--current-generation",
                "1",
                input=agent_list,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_excludes_records_absent_from_agent_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "delegations.json"
            self._write_records(
                records,
                [
                    {
                        "generation": 1,
                        "role": "review",
                        "agent_name": "hd-bbbbbbbb-review-1",
                        "pane_id": "wD:p1",
                        "mode": "agent",
                        "state": "active",
                    }
                ],
            )
            # Agent already vanished from `agent list`.
            agent_list = self._agent_list([])
            result = run_helper(
                "select-orphans",
                "--agent-list-json",
                "-",
                "--records",
                str(records),
                "--current-generation",
                "2",
                input=agent_list,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")


# ---------------------------------------------------------------------------
# build-launch-args (AC6-AC11)
# ---------------------------------------------------------------------------


class BuildLaunchArgsTests(unittest.TestCase):
    def _make_toolchain_codex(self, root: Path, label: str) -> tuple[Path, Path]:
        """Create <root>/<label>/mise/installs/node/1.0.0/bin/codex.

        Returns (codex_path, toolchain_root).
        """
        bin_dir = root / label / "mise" / "installs" / "node" / "1.0.0" / "bin"
        codex_path = bin_dir / "codex"
        make_executable(codex_path, "#!/bin/sh\necho fake-codex\n")
        return codex_path, (root / label / "mise").resolve()

    def _make_toolchain_codex_symlink(
        self, root: Path, label: str
    ) -> tuple[Path, Path, Path]:
        """Create <root>/<label>/mise/installs/node/1.0.0/lib/pkg/bin/codex.js
        with a `bin/codex -> ../lib/pkg/bin/codex.js` symlink alongside it,
        mirroring how mise-managed npm installs of @openai/codex actually
        lay out on disk (the real executable is `codex.js`; there is no
        file literally named `codex` in its own directory).

        Returns (symlink_path, resolved_target_path, toolchain_root).
        """
        version_dir = root / label / "mise" / "installs" / "node" / "1.0.0"
        real_bin_dir = version_dir / "lib" / "pkg" / "bin"
        real_codex = real_bin_dir / "codex.js"
        make_executable(real_codex, "#!/usr/bin/env node\n")

        symlink_bin_dir = version_dir / "bin"
        symlink_bin_dir.mkdir(parents=True, exist_ok=True)
        symlink_path = symlink_bin_dir / "codex"
        symlink_path.symlink_to(Path("..") / "lib" / "pkg" / "bin" / "codex.js")

        return symlink_path, real_codex.resolve(), (root / label / "mise").resolve()

    def test_normal_profile_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path, toolchain_root = self._make_toolchain_codex(tmp_path, "a")

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "hdreview",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = result.stdout

            # AC6: --sandbox never appears.
            self.assertNotIn("--sandbox", output)

            # AC7: required profile settings and read-allow list (":minimal"
            # + toolchain root only), scratch write, no deny globs, no
            # brew root / ~/.codex.
            self.assertIn('default_permissions="hdreview"', output)
            self.assertIn('approval_policy="never"', output)
            self.assertIn('model_reasoning_effort="high"', output)
            self.assertIn('":minimal"="read"', output)
            self.assertIn(f'"{toolchain_root}"="read"', output)
            self.assertIn(f'"{scratch}"={{"."="write"}}', output)
            self.assertNotIn('"**"="deny"', output)
            self.assertNotIn("linuxbrew", output)
            self.assertNotIn(".codex", output)

            # AC11: no single quotes or embedded newlines in any output line.
            for line in output.splitlines():
                self.assertNotIn("'", line)

    def test_root_follows_resolved_codex_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            for label in ("a", "b"):
                scratch = tmp_path / f"scratch-{label}"
                scratch.mkdir()
                codex_path, toolchain_root = self._make_toolchain_codex(tmp_path, label)
                env = os.environ.copy()
                env["PATH"] = f"{codex_path.parent}{os.pathsep}{env.get('PATH', '')}"

                result = run_helper(
                    "build-launch-args",
                    "--scratch",
                    str(scratch),
                    "--profile-name",
                    "p",
                    "--repo-root",
                    str(repo_root),
                    env=env,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'"{toolchain_root}"="read"', result.stdout)

    def test_fails_when_codex_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            empty_bin = tmp_path / "empty-bin"
            empty_bin.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty_bin)

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(tmp_path / "scratch"),
                "--profile-name",
                "p",
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_ancestor_guard_rejects_home_local_share(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            repo_root = home / ".local" / "share" / "chezmoi"
            repo_root.mkdir(parents=True)
            # codex resolves under $HOME/.local/share/installs/... so the
            # derived toolchain root is $HOME/.local/share itself.
            codex_path = (
                home
                / ".local"
                / "share"
                / "installs"
                / "node"
                / "1.0.0"
                / "bin"
                / "codex"
            )

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(tmp_path / "scratch"),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
                env={**os.environ, "HOME": str(home)},
            )
            self.assertNotEqual(result.returncode, 0)

    def test_ancestor_guard_rejects_home_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            codex_path = home / "installs" / "node" / "1.0.0" / "bin" / "codex"

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(tmp_path / "scratch"),
                "--profile-name",
                "p",
                "--repo-root",
                str(tmp_path / "repo"),
                "--codex-path",
                str(codex_path),
                env={**os.environ, "HOME": str(home)},
            )
            self.assertNotEqual(result.returncode, 0)

    def test_ancestor_guard_rejects_filesystem_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            codex_path = Path("/installs/node/1.0.0/bin/codex")

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(tmp_path / "scratch"),
                "--profile-name",
                "p",
                "--repo-root",
                str(tmp_path / "repo"),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_ancestor_guard_rejects_repo_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "workspace" / "repo"
            repo_root.mkdir(parents=True)
            # toolchain root resolves to a direct ancestor of repo_root.
            codex_path = (
                tmp_path / "workspace" / "installs" / "node" / "1.0.0" / "bin" / "codex"
            )

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(tmp_path / "scratch"),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_env_out_uses_unresolved_symlink_parent(self) -> None:
        """F2-a: when codex is a symlink whose resolved target lives in a
        directory with no file literally named `codex` (e.g. only
        `codex.js`), --env-out must still point PATH at a directory that
        actually contains a `codex` executable -- the symlink's own
        (unresolved) parent, not the resolved target's parent."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            symlink_path, resolved_path, _ = self._make_toolchain_codex_symlink(
                tmp_path, "a"
            )
            env_out = tmp_path / "env-out.txt"

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(symlink_path),
                "--env-out",
                str(env_out),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            content = env_out.read_text(encoding="utf-8")
            path_line = content.splitlines()[0]
            self.assertTrue(path_line.startswith(f"PATH={symlink_path.parent}"))
            # The resolved target's directory (which has no file literally
            # named "codex") must not be what ends up on PATH.
            self.assertNotIn(str(resolved_path.parent), path_line.split(os.pathsep)[0])
            self.assertTrue((symlink_path.parent / "codex").exists())
            self.assertFalse((resolved_path.parent / "codex").exists())

    def test_toolchain_root_still_resolved_through_symlink(self) -> None:
        """F2-b: toolchain-root derivation (and the ancestor guard applied
        to it) must keep following symlinks to the real mise install root,
        unaffected by the F2-a fix to env-out's PATH."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            symlink_path, _, toolchain_root = self._make_toolchain_codex_symlink(
                tmp_path, "a"
            )

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(symlink_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'"{toolchain_root}"="read"', result.stdout)

    def test_env_out_writes_expanded_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path, _ = self._make_toolchain_codex(tmp_path, "a")
            env_out = tmp_path / "env-out.txt"

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
                "--env-out",
                str(env_out),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            content = env_out.read_text(encoding="utf-8")
            self.assertTrue(content.startswith(f"PATH={codex_path.parent}"))

    def test_rejects_profile_name_with_single_quote(self) -> None:
        """G3-a (RED case): a profile name containing a single quote must
        not be emitted at all -- previously it was printed verbatim, which
        would corrupt a single-quote-wrapped `-c` argument downstream."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path, _ = self._make_toolchain_codex(tmp_path, "a")
            env_out = tmp_path / "env-out.txt"

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "hd'review",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
                "--env-out",
                str(env_out),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(env_out.exists())

    def test_normal_profile_name_still_writes_env_out(self) -> None:
        """G3-b: normal (no quote/newline) input keeps producing --env-out
        output, so the new guard in G3-a does not regress the happy path."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path, _ = self._make_toolchain_codex(tmp_path, "a")
            env_out = tmp_path / "env-out.txt"

            result = run_helper(
                "build-launch-args",
                "--scratch",
                str(scratch),
                "--profile-name",
                "hdreview",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
                "--env-out",
                str(env_out),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(env_out.exists())


# ---------------------------------------------------------------------------
# verify-profile (AC12)
# ---------------------------------------------------------------------------


class VerifyProfileTests(unittest.TestCase):
    def _make_fake_codex_sandbox(
        self, tmp_path: Path, exit_code: int, stderr_message: str
    ) -> Path:
        bin_dir = (
            tmp_path / "toolchain" / "mise" / "installs" / "node" / "1.0.0" / "bin"
        )
        codex_path = bin_dir / "codex"
        script = (
            "#!/bin/sh\n"
            'if [ "$1" = sandbox ]; then\n'
            f"  >&2 printf '%s\\n' {shlex.quote(stderr_message)}\n"
            f"  exit {exit_code}\n"
            "fi\n"
            "exit 0\n"
        )
        make_executable(codex_path, script)
        return codex_path

    def _make_fake_codex_sandbox_target_aware(
        self, tmp_path: Path, scratch: Path, positive_exit: int, negative_exit: int
    ) -> Path:
        """Fake codex whose canary exit code depends on the probed target:
        the canary's last argv is `test -e <target>`; if <target> lives
        under `scratch`, exit `positive_exit`, otherwise `negative_exit`.
        Lets a single fixture drive the two-stage canary independently for
        its positive and negative legs."""
        bin_dir = (
            tmp_path / "toolchain" / "mise" / "installs" / "node" / "1.0.0" / "bin"
        )
        codex_path = bin_dir / "codex"
        script = (
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "if len(sys.argv) > 1 and sys.argv[1] == 'sandbox':\n"
            f"    scratch = {str(scratch)!r}\n"
            "    last = sys.argv[-1]\n"
            "    if last.startswith('test -e ' + scratch):\n"
            f"        sys.exit({positive_exit})\n"
            "    else:\n"
            f"        sys.exit({negative_exit})\n"
            "sys.exit(0)\n"
        )
        make_executable(codex_path, script)
        return codex_path

    def _make_isolation_free_fake_codex(self, tmp_path: Path) -> Path:
        """Fake codex that applies zero isolation: it execs whatever comes
        after the literal `--` argument, so the canary's `test -e <target>`
        runs directly against the real filesystem. Used to prove
        verify-profile does not silently report "isolated" just because a
        specific hardcoded target happens to be absent (G1)."""
        bin_dir = (
            tmp_path / "toolchain" / "mise" / "installs" / "node" / "1.0.0" / "bin"
        )
        codex_path = bin_dir / "codex"
        script = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "argv = sys.argv[1:]\n"
            "if '--' in argv:\n"
            "    idx = argv.index('--')\n"
            "    cmd = argv[idx + 1:]\n"
            "    os.execvp(cmd[0], cmd)\n"
            "sys.exit(1)\n"
        )
        make_executable(codex_path, script)
        return codex_path

    def _make_isolation_free_fake_codex_honoring_cwd(self, tmp_path: Path) -> Path:
        """Same as `_make_isolation_free_fake_codex`, but it also honours the
        `-C <dir>` flag by chdir-ing before exec, like the real `codex
        sandbox` does. Needed to expose targets that are only safe when
        expressed as absolute paths (N1)."""
        bin_dir = (
            tmp_path / "toolchain2" / "mise" / "installs" / "node" / "1.0.0" / "bin"
        )
        codex_path = bin_dir / "codex"
        script = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "argv = sys.argv[1:]\n"
            "if '-C' in argv:\n"
            "    os.chdir(argv[argv.index('-C') + 1])\n"
            "if '--' in argv:\n"
            "    idx = argv.index('--')\n"
            "    cmd = argv[idx + 1:]\n"
            "    os.execvp(cmd[0], cmd)\n"
            "sys.exit(1)\n"
        )
        make_executable(codex_path, script)
        return codex_path

    def test_relative_repo_root_is_not_fail_open(self) -> None:
        """N1: `--repo-root` given as a relative path must not silently
        report "isolated". The canary runs with cwd moved to the scratch
        dir (`codex sandbox -C <scratch>`), so a relative negative-canary
        target resolves against the scratch dir, is always absent, and used
        to be read as "invisible" even with zero isolation in effect."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("# repo\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_isolation_free_fake_codex_honoring_cwd(tmp_path)

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                "repo",
                "--codex-path",
                str(codex_path),
                cwd=tmp_path,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_dangling_symlink_first_entry_is_not_fail_open(self) -> None:
        """N2: the negative-canary target is picked from `repo_root`'s
        entries. A dangling symlink sorting first would make `test -e`
        nonzero even with zero isolation, which reads as "invisible".
        Entries must be filtered by actual existence."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "AAA-dangling").symlink_to(tmp_path / "nonexistent")
            (repo_root / "README.md").write_text("# repo\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_isolation_free_fake_codex(tmp_path)

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_nonzero_canary_means_isolated(self) -> None:
        """F1-c: two-stage canary, positive leg (scratch visible) exits 0
        and negative leg (repo CLAUDE.md invisible) exits nonzero ->
        isolation confirmed. Updated from the pre-fix single-canary
        fixture, which could not distinguish this from a canary that fails
        to parse its own arguments (see test_canary_parse_error_exit_is_nonzero)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox_target_aware(
                tmp_path, scratch, positive_exit=0, negative_exit=1
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_canary_parse_error_exit_is_nonzero(self) -> None:
        """F1-a (RED case): canary exits 2, as a codex predating
        --permission-profile would when clap rejects the unknown flag.
        Before the fix, any nonzero exit code was read as "isolated"; this
        must now be nonzero since the positive leg cannot be confirmed
        either."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path,
                exit_code=2,
                stderr_message="error: unexpected argument '--permission-profile'",
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_positive_canary_failure_is_nonzero(self) -> None:
        """F1-b: both canary legs fail (positive leg cannot confirm scratch
        is visible) -> isolation cannot be confirmed -> nonzero."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path, exit_code=1, stderr_message="No such file or directory"
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_zero_canary_means_not_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path, exit_code=0, stderr_message=""
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_canary_launch_failure_is_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            # G1: repo_root needs an entry so the negative-canary target
            # selection succeeds and this test still exercises codex exec
            # failure, not the (separate) "no target could be selected"
            # path covered by test_missing_repo_root_is_nonzero /
            # test_empty_repo_root_is_nonzero.
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            # codex path resolves under a valid mise-style layout but the
            # binary itself was never created -> exec fails.
            missing_codex = (
                tmp_path
                / "toolchain"
                / "mise"
                / "installs"
                / "node"
                / "1.0.0"
                / "bin"
                / "codex"
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(missing_codex),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_ja_locale_message_does_not_flip_the_result(self) -> None:
        """A zero-exit canary that prints a ja_JP-looking success message
        must still be judged unsafe (non-zero) -- the message is never
        inspected."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path,
                exit_code=0,
                stderr_message="そのようなファイルやディレクトリはありません",
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_no_isolation_and_no_claude_md_is_detected_as_not_isolated(self) -> None:
        """G1-a (RED case): with zero isolation and a repo_root that has no
        CLAUDE.md (but does have some other entry), verify-profile must not
        silently report "isolated" just because the previous hardcoded
        negative-canary target (CLAUDE.md) happens to be absent. Before the
        fix, this returned 0 (fail-open); after the fix it must be nonzero."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "README.md").write_text("# repo\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_isolation_free_fake_codex(tmp_path)

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_no_isolation_with_claude_md_is_detected_as_not_isolated(self) -> None:
        """G1-b: zero isolation is still detected even when repo_root does
        have a CLAUDE.md (the pre-fix hardcoded target)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            (repo_root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_isolation_free_fake_codex(tmp_path)

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_missing_repo_root_is_nonzero(self) -> None:
        """G1-c: repo_root does not exist at all -> no target can be
        selected for the negative canary leg -> fail closed."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"  # deliberately never created
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path, exit_code=0, stderr_message=""
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_empty_repo_root_is_nonzero(self) -> None:
        """G1-c: repo_root exists but has no entries -> no target can be
        selected for the negative canary leg -> fail closed."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            repo_root.mkdir()
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            codex_path = self._make_fake_codex_sandbox(
                tmp_path, exit_code=0, stderr_message=""
            )

            result = run_helper(
                "verify-profile",
                "--scratch",
                str(scratch),
                "--profile-name",
                "p",
                "--repo-root",
                str(repo_root),
                "--codex-path",
                str(codex_path),
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
