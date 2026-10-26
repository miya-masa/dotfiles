from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HERDR_ZSH = ROOT / "dot_zsh/herdr.zsh"
LOCAL_OVERRIDE = 'shell_environment_policy.set.HERDR_ENV="1"'


def make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class HerdrCodexWrapperTests(unittest.TestCase):
    def run_codex(
        self,
        args: list[str],
        *,
        source_herdr_env: str | None = "1",
        unset_after_source: bool = False,
        fake_exit: int = 0,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            capture_path = root / "capture.json"
            make_executable(
                bin_dir / "codex",
                "#!/usr/bin/env python3\n"
                "import json\n"
                "import os\n"
                "from pathlib import Path\n"
                "import sys\n"
                "Path(os.environ['HERDR_CAPTURE']).write_text(\n"
                "    json.dumps({\n"
                "        'argv': sys.argv[1:],\n"
                "        'env': {'HERDR_ENV': os.environ.get('HERDR_ENV')},\n"
                "    }),\n"
                "    encoding='utf-8',\n"
                ")\n"
                "raise SystemExit(int(os.environ.get('HERDR_FAKE_EXIT', '0')))\n",
            )

            environment = os.environ.copy()
            environment["PATH"] = f"{bin_dir}{os.pathsep}{environment['PATH']}"
            environment["HERDR_CAPTURE"] = str(capture_path)
            environment["HERDR_FAKE_EXIT"] = str(fake_exit)
            if source_herdr_env is None:
                environment.pop("HERDR_ENV", None)
            else:
                environment["HERDR_ENV"] = source_herdr_env

            script = 'source "$1"\nshift\n'
            if unset_after_source:
                script += "unset HERDR_ENV\n"
            script += 'codex "$@"\n'
            result = subprocess.run(
                ["zsh", "-f", "-c", script, "herdr-test", str(HERDR_ZSH), *args],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            return result, json.loads(capture_path.read_text(encoding="utf-8"))

    def assert_injected(self, args: list[str]) -> None:
        result, capture = self.run_codex(args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture["argv"], ["-c", LOCAL_OVERRIDE, *args])
        self.assertEqual(capture["env"]["HERDR_ENV"], "1")

    def assert_passthrough(self, args: list[str]) -> None:
        result, capture = self.run_codex(args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture["argv"], args)
        self.assertEqual(capture["env"]["HERDR_ENV"], "1")

    def test_wraps_tui_invocations_and_preserves_arguments(self) -> None:
        cases = [
            ("empty", []),
            ("prompt", ["hello world", "queue"]),
            ("empty prompt", [""]),
            ("metacharacters", ["$(touch should-not-run); *"]),
            ("resume", ["resume", "session-1"]),
            ("fork", ["fork", "--last"]),
            ("boolean flag", ["--strict-config", "resume"]),
            ("value named management command", ["--model", "queue", "prompt"]),
            ("attached value named management command", ["-mqueue", "prompt"]),
            ("equal value named management command", ["--model=queue", "prompt"]),
            ("image consumes queue", ["-i", "a.png", "queue"]),
            ("attached image with prompt", ["-ia.png", "hello world"]),
            ("equal image with prompt", ["--image=a.png", "hello world"]),
            ("image stops at double dash", ["-i", "a.png", "--", "queue"]),
            ("double dash prompt", ["--", "queue"]),
            ("double dash help is prompt", ["--", "--help"]),
        ]
        for name, args in cases:
            with self.subTest(name=name):
                self.assert_injected(args)

    def test_passes_management_commands_through(self) -> None:
        management_commands = [
            "agents",
            "exec",
            "e",
            "review",
            "login",
            "logout",
            "mcp",
            "plugin",
            "app-server",
            "exec-server",
            "remote-control",
            "completion",
            "update",
            "doctor",
            "sandbox",
            "debug",
            "apply",
            "a",
            "queue",
            "archive",
            "delete",
            "migrate-rollouts",
            "unarchive",
            "cloud",
            "features",
            "help",
        ]
        for command in management_commands:
            with self.subTest(command=command):
                self.assert_passthrough([command, "--example"])

    def test_passes_root_options_and_management_commands_through(self) -> None:
        global_flags = [
            "--strict-config",
            "--oss",
            "--approve-for-me",
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
            "--worktree",
            "--search",
            "--no-alt-screen",
        ]
        cases = [
            ("boolean flags", [*global_flags, "queue", "--example"]),
            ("separated value before command", ["--model", "queue", "queue"]),
            ("equal value before command", ["--config=queue", "queue"]),
            ("attached short value before command", ["-cqueue", "queue"]),
            ("image boundary", ["-i", "a.png", "--no-alt-screen", "queue"]),
            ("multiple image boundary", ["-i", "a.png", "b.png", "--no-alt-screen", "queue"]),
            ("attached image boundary", ["-ia.png", "--no-alt-screen", "queue"]),
            ("equal image boundary", ["--image=a.png", "--no-alt-screen", "queue"]),
            ("attached image then agents", ["-ia.png", "agents"]),
            ("equal image then exec", ["--image=a.png", "exec", "prompt"]),
            (
                "multiple image values and command help",
                ["-i", "a", "b", "--no-alt-screen", "queue", "--help"],
            ),
            ("image consumes queue before root help", ["-i", "a", "queue", "--help"]),
            ("unknown root option", ["--unknown-root-option", "queue"]),
            ("missing value", ["--model"]),
            ("missing short value", ["-m"]),
        ]
        for name, args in cases:
            with self.subTest(name=name):
                self.assert_passthrough(args)

    def test_passes_explicit_remote_help_and_version_anywhere_before_double_dash(self) -> None:
        cases = [
            ["--remote"],
            ["--remote=staging"],
            ["resume", "session-1", "--remote"],
            ["resume", "session-1", "--remote=staging"],
            ["prompt", "--remote"],
            ["resume", "-h"],
            ["resume", "--help"],
            ["resume", "-V"],
            ["resume", "--version"],
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assert_passthrough(args)

    def test_treats_remote_help_and_version_after_double_dash_as_prompt(self) -> None:
        for args in (["--", "--remote"], ["--", "--version"], ["--", "-h"]):
            with self.subTest(args=args):
                self.assert_injected(args)

    def test_source_and_call_time_herdr_environment_gates_the_wrapper(self) -> None:
        for source_herdr_env in (None, "0"):
            with self.subTest(source_herdr_env=source_herdr_env):
                with tempfile.TemporaryDirectory() as temporary:
                    environment = os.environ.copy()
                    if source_herdr_env is None:
                        environment.pop("HERDR_ENV", None)
                    else:
                        environment["HERDR_ENV"] = source_herdr_env
                    result = subprocess.run(
                        [
                            "zsh",
                            "-f",
                            "-c",
                            'source "$1"\n(( $+functions[codex] ))',
                            "herdr-test",
                            str(HERDR_ZSH),
                        ],
                        text=True,
                        capture_output=True,
                        env=environment,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 1)
                args = ["--model", "queue", "resume", "session-1"]
                result, capture = self.run_codex(args, source_herdr_env=source_herdr_env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(capture["argv"], args)

        result, capture = self.run_codex(
            ["prompt"], source_herdr_env="1", unset_after_source=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture["argv"], ["prompt"])
        self.assertIsNone(capture["env"]["HERDR_ENV"])

    def test_propagates_codex_exit_code(self) -> None:
        result, capture = self.run_codex(["prompt"], fake_exit=23)
        self.assertEqual(result.returncode, 23)
        self.assertEqual(capture["argv"], ["-c", LOCAL_OVERRIDE, "prompt"])

    def test_preserves_user_override_order(self) -> None:
        args = ["-c", 'shell_environment_policy.inherit="core"', "resume", "session-1",
                "-c", 'shell_environment_policy.set.HERDR_ENV="0"']
        self.assert_injected(args)


if __name__ == "__main__":
    unittest.main()
