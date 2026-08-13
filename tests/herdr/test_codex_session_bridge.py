from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "dot_local/bin/executable_herdr-codex-session-bridge"
INSTALLER = ROOT / ".chezmoiscripts/run_onchange_after_17-install-herdr-integrations.sh"


def make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class CodexSessionBridgeTests(unittest.TestCase):
    def test_forwards_prompt_with_transcript_as_session_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex"
            codex_home.mkdir()
            input_path = root / "input.json"
            action_path = root / "action"
            marker_path = root / "marker"
            make_executable(
                codex_home / "herdr-agent-state.sh",
                "#!/bin/sh\n"
                f"printf '%s' \"$1\" > {shlex.quote(str(action_path))}\n"
                f"cat > {shlex.quote(str(input_path))}\n"
                f"printf '%s' \"$HERDR_TEST_MARKER\" > {shlex.quote(str(marker_path))}\n",
            )

            event = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "session-1",
                "transcript_path": "/tmp/rollout.jsonl",
                "source": "user",
                "extra": {"preserve": True},
            }
            environment = os.environ.copy()
            environment.update(
                {
                    "CODEX_HOME": str(codex_home),
                    "HERDR_TEST_MARKER": "forwarded",
                }
            )
            result = subprocess.run(
                [sys.executable, str(BRIDGE)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(action_path.read_text(encoding="utf-8"), "session")
            self.assertEqual(marker_path.read_text(encoding="utf-8"), "forwarded")
            transformed = json.loads(input_path.read_text(encoding="utf-8"))
            self.assertEqual(transformed["hook_event_name"], "SessionStart")
            self.assertEqual(transformed["session_id"], event["session_id"])
            self.assertEqual(
                transformed["transcript_path"], event["transcript_path"]
            )
            self.assertEqual(transformed["extra"], event["extra"])

    def test_rejects_events_without_the_required_identity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex"
            codex_home.mkdir()
            called = root / "called"
            make_executable(
                codex_home / "herdr-agent-state.sh",
                "#!/bin/sh\n"
                f"touch {shlex.quote(str(called))}\n",
            )
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            events = (
                {"hook_event_name": "SessionStart", "session_id": "s", "transcript_path": "/tmp/t"},
                {"hook_event_name": "UserPromptSubmit", "session_id": "s", "transcript_path": None},
                {"hook_event_name": "UserPromptSubmit", "session_id": "s", "transcript_path": ""},
                {"hook_event_name": "UserPromptSubmit", "session_id": None, "transcript_path": "/tmp/t"},
                {"hook_event_name": "UserPromptSubmit", "session_id": "", "transcript_path": "/tmp/t"},
                {"hook_event_name": "UserPromptSubmit", "transcript_path": "/tmp/t"},
            )
            for event in events:
                with self.subTest(event=event):
                    result = subprocess.run(
                        [sys.executable, str(BRIDGE)],
                        input=json.dumps(event),
                        text=True,
                        capture_output=True,
                        env=environment,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(called.exists())

    def test_propagates_installed_hook_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex"
            codex_home.mkdir()
            make_executable(
                codex_home / "herdr-agent-state.sh",
                "#!/bin/sh\nexit 17\n",
            )
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            result = subprocess.run(
                [sys.executable, str(BRIDGE)],
                input=json.dumps(
                    {
                        "hook_event_name": "UserPromptSubmit",
                        "session_id": "session-1",
                        "transcript_path": "/tmp/rollout.jsonl",
                    }
                ),
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 17)


class HerdrIntegrationInstallerTests(unittest.TestCase):
    def run_installer(self, home: Path, codex_home: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "CODEX_HOME": str(codex_home),
                "PATH": f"{bin_dir}{os.pathsep}{environment['PATH']}",
            }
        )
        return subprocess.run(
            ["bash", str(INSTALLER)],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )

    def write_fake_herdr(self, bin_dir: Path) -> None:
        make_executable(
            bin_dir / "herdr",
            "#!/bin/sh\n"
            "if [ \"$1\" = integration ] && [ \"$2\" = status ]; then\n"
            "  printf '%s\\n' 'claude: current (v7) (/tmp/claude)' 'codex: current (v7) (/tmp/codex)'\n"
            "fi\n",
        )

    def test_merges_bridge_once_and_preserves_other_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            codex_home = home / ".codex"
            bin_dir = root / "bin"
            codex_home.mkdir(parents=True)
            bin_dir.mkdir()
            self.write_fake_herdr(bin_dir)
            original = {
                "hooks": {
                    "SessionStart": [
                        {"hooks": [{"command": "bash herdr-agent-state.sh session"}]}
                    ],
                    "UserPromptSubmit": [
                        {"hooks": [{"command": "bash unrelated-hook"}]}
                    ],
                },
                "unrelated": {"keep": True},
            }
            hooks_path = codex_home / "hooks.json"
            hooks_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")

            first = self.run_installer(home, codex_home, bin_dir)
            self.assertEqual(first.returncode, 0, first.stderr)
            merged = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertEqual(merged["unrelated"], original["unrelated"])
            self.assertEqual(
                merged["hooks"]["UserPromptSubmit"][0],
                original["hooks"]["UserPromptSubmit"][0],
            )
            self.assertEqual(len(merged["hooks"]["UserPromptSubmit"]), 2)
            bridge_command = shlex.quote(
                str(home / ".local/bin/herdr-codex-session-bridge")
            )
            bridge_groups = [
                group
                for group in merged["hooks"]["UserPromptSubmit"]
                if any(
                    hook.get("command") == bridge_command
                    for hook in group.get("hooks", [])
                    if isinstance(hook, dict)
                )
            ]
            self.assertEqual(len(bridge_groups), 1)
            self.assertEqual(
                bridge_groups[0]["hooks"][0],
                {"command": bridge_command, "timeout": 10, "type": "command"},
            )

            installed_bridge = home / ".local/bin/herdr-codex-session-bridge"
            installed_bridge.parent.mkdir(parents=True)
            shutil.copy2(BRIDGE, installed_bridge)
            installed_bridge.chmod(installed_bridge.stat().st_mode | stat.S_IXUSR)
            forwarded = root / "forwarded.json"
            make_executable(
                codex_home / "herdr-agent-state.sh",
                "#!/bin/sh\n"
                f"cat > {shlex.quote(str(forwarded))}\n",
            )
            executed = subprocess.run(
                bridge_command,
                shell=True,
                input=json.dumps(
                    {
                        "hook_event_name": "UserPromptSubmit",
                        "session_id": "session-1",
                        "transcript_path": "/tmp/rollout.jsonl",
                    }
                ),
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": str(home), "CODEX_HOME": str(codex_home)},
                check=False,
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)
            self.assertEqual(
                json.loads(forwarded.read_text(encoding="utf-8"))["hook_event_name"],
                "SessionStart",
            )

            second = self.run_installer(home, codex_home, bin_dir)
            self.assertEqual(second.returncode, 0, second.stderr)
            rerun = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertEqual(rerun, merged)
            self.assertEqual(len(rerun["hooks"]["UserPromptSubmit"]), 2)

    def test_rejects_malformed_hooks_without_overwriting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            codex_home = home / ".codex"
            bin_dir = root / "bin"
            codex_home.mkdir(parents=True)
            bin_dir.mkdir()
            self.write_fake_herdr(bin_dir)
            hooks_path = codex_home / "hooks.json"
            hooks_path.write_text("[]\n", encoding="utf-8")

            result = self.run_installer(home, codex_home, bin_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(hooks_path.read_text(encoding="utf-8"), "[]\n")


if __name__ == "__main__":
    unittest.main()
