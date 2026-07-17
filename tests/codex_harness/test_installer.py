from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / ".chezmoiscripts/run_onchange_after_35-configure-codex.sh.tmpl"
REQUIRED_WRITABLE_ROOTS = [
    str(Path.home() / "go"),
    "/tmp/claude",
]
REMOVED_WRITABLE_ROOT = str(Path.home() / "claude" / "skills")
DISABLED_SKILLS = {
    "feature-development",
    "bugfix",
    "spec-review",
    "context-budget",
    "skill-stocktake",
    "handoff",
    "writing-gpt-prompts",
    "skill-creator",
}
LEGACY_AGENT_NAMES = {
    "agent_luna_worker",
    "agent_explorer",
    "agent_implementer",
    "agent_reviewer",
    "agent_verifier",
    "agent_investigator",
    "agent_decision_reviewer",
}


def run_configure(config: Path, override: str = "") -> subprocess.CompletedProcess[str]:
    command = f'source "$1"\n{override}\nconfigure_codex "$2"'
    return subprocess.run(
        ["bash", "-c", command, "_", str(INSTALLER), str(config)],
        text=True,
        capture_output=True,
        check=False,
    )


def run_installer(home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        ["bash", str(INSTALLER)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def load_config(config: Path) -> dict:
    with config.open("rb") as config_file:
        return tomllib.load(config_file)


def artifacts(config: Path) -> list[Path]:
    return list(config.parent.glob(f"{config.name}.codex-*"))


def disabled_skill_names(config: dict) -> set[str]:
    entries = config["skills"]["config"]
    return {
        Path(entry["path"]).parent.name
        for entry in entries
        if entry.get("enabled") is False
    }


def assert_required_config(config: dict) -> None:
    assert config["model"] == "gpt-5.6-sol"
    assert config["model_reasoning_effort"] == "medium"
    assert config["plan_mode_reasoning_effort"] == "high"
    assert config["approval_policy"] == "never"
    assert config["model_auto_compact_token_limit"] == 260_000
    assert config["model_auto_compact_token_limit_scope"] == "total"
    assert config["sandbox_workspace_write"]["network_access"] is True
    assert all(
        root in config["sandbox_workspace_write"]["writable_roots"]
        for root in REQUIRED_WRITABLE_ROOTS
    )
    assert REMOVED_WRITABLE_ROOT not in config["sandbox_workspace_write"]["writable_roots"]
    assert "multi_agent" not in config.get("features", {})
    agents = config["agents"]
    assert "max_depth" not in agents
    assert "max_threads" not in agents
    assert not LEGACY_AGENT_NAMES.intersection(agents)
    assert agents["reviewer"] == {
        "description": "Read-only artifact reviewer for correctness, adversarial risks, product fit, and simplicity.",
        "config_file": "agents/reviewer.toml",
    }
    assert disabled_skill_names(config) == DISABLED_SKILLS


def test_existing_config_preserves_unknown_values_mode_and_is_idempotent(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        'model = "old"\nunknown = "preserve"\n\n'
        "[sandbox_workspace_write]\n"
        f'writable_roots = ["/custom/root", "{REQUIRED_WRITABLE_ROOTS[0]}", '
        f'"{REMOVED_WRITABLE_ROOT}"]\n\n'
        "[features]\ncustom_feature = true\nmulti_agent = true\n\n"
        "[agents]\nmax_depth = 1\nmax_threads = 6\n\n"
        "[agents.agent_explorer]\nconfig_file = \"legacy.toml\"\n\n"
        "[agents.my_agent]\nconfig_file = \"agents/custom.toml\"\n\n"
        "[unrelated]\nnested = 42\n",
        encoding="utf-8",
    )
    config.chmod(0o640)

    first = run_configure(config)
    assert first.returncode == 0, first.stderr
    first_bytes = config.read_bytes()
    parsed = load_config(config)
    assert_required_config(parsed)
    assert parsed["unknown"] == "preserve"
    assert parsed["sandbox_workspace_write"]["writable_roots"] == [
        "/custom/root",
        REQUIRED_WRITABLE_ROOTS[0],
        *REQUIRED_WRITABLE_ROOTS[1:],
    ]
    assert parsed["features"]["custom_feature"] is True
    assert parsed["agents"]["my_agent"] == {"config_file": "agents/custom.toml"}
    assert parsed["unrelated"] == {"nested": 42}
    assert stat.S_IMODE(config.stat().st_mode) == 0o640
    assert artifacts(config) == []

    second = run_configure(config)
    assert second.returncode == 0, second.stderr
    assert config.read_bytes() == first_bytes
    assert stat.S_IMODE(config.stat().st_mode) == 0o640
    assert artifacts(config) == []


def test_non_managed_native_agent_limits_are_preserved(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[features]\nmulti_agent = false\n\n"
        "[agents]\nmax_depth = 2\nmax_threads = 3\n",
        encoding="utf-8",
    )

    result = run_configure(config)

    assert result.returncode == 0, result.stderr
    parsed = load_config(config)
    assert parsed["features"]["multi_agent"] is False
    assert parsed["agents"]["max_depth"] == 2
    assert parsed["agents"]["max_threads"] == 3


def test_preexisting_skill_config_is_preserved(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    existing_path = Path.home() / ".agents/skills/feature-development/SKILL.md"
    config.write_text(
        "[[skills.config]]\n"
        f'path = "{existing_path}"\n'
        "enabled = false\n",
        encoding="utf-8",
    )

    first = run_configure(config)
    assert first.returncode == 0, first.stderr
    first_bytes = config.read_bytes()
    entries = load_config(config)["skills"]["config"]
    assert sum(entry["path"] == str(existing_path) for entry in entries) == 2

    second = run_configure(config)
    assert second.returncode == 0, second.stderr
    assert config.read_bytes() == first_bytes


def test_skill_config_after_legacy_agent_is_preserved(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    custom_skill = tmp_path / "custom-skill/SKILL.md"
    config.write_text(
        "[agents.agent_explorer]\n"
        'config_file = "agents/legacy.toml"\n\n'
        "[[skills.config]]\n"
        f'path = "{custom_skill}"\n'
        "enabled = true\n",
        encoding="utf-8",
    )

    first = run_configure(config)
    assert first.returncode == 0, first.stderr
    first_bytes = config.read_bytes()
    entries = load_config(config)["skills"]["config"]
    assert {"path": str(custom_skill), "enabled": True} in entries

    second = run_configure(config)
    assert second.returncode == 0, second.stderr
    assert config.read_bytes() == first_bytes


def test_existing_writable_roots_keep_order_and_do_not_duplicate_required_roots(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[sandbox_workspace_write]\n"
        f'writable_roots = ["/first", "{REQUIRED_WRITABLE_ROOTS[1]}", "/second"]\n',
        encoding="utf-8",
    )

    result = run_configure(config)

    assert result.returncode == 0, result.stderr
    assert load_config(config)["sandbox_workspace_write"]["writable_roots"] == [
        "/first",
        REQUIRED_WRITABLE_ROOTS[1],
        "/second",
        REQUIRED_WRITABLE_ROOTS[0],
    ]


def test_missing_config_is_created_with_private_mode(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"

    result = run_configure(config)

    assert result.returncode == 0, result.stderr
    assert_required_config(load_config(config))
    assert stat.S_IMODE(config.stat().st_mode) == 0o600
    assert artifacts(config) == []


def test_multiline_writable_roots_are_preserved_and_update_is_idempotent(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[sandbox_workspace_write]\n"
        "writable_roots = [\n"
        '  "/custom/one",\n'
        f'  "{REMOVED_WRITABLE_ROOT}",\n'
        '  "/custom/two",\n'
        "]\n",
        encoding="utf-8",
    )

    first = run_configure(config)
    assert first.returncode == 0, first.stderr
    first_bytes = config.read_bytes()
    assert load_config(config)["sandbox_workspace_write"]["writable_roots"] == [
        "/custom/one",
        "/custom/two",
        *REQUIRED_WRITABLE_ROOTS,
    ]

    second = run_configure(config)
    assert second.returncode == 0, second.stderr
    assert config.read_bytes() == first_bytes


def test_only_codex_superpowers_symlink_is_removed(tmp_path: Path) -> None:
    codex_skills = tmp_path / ".codex/superpowers/skills"
    codex_skills.mkdir(parents=True)
    shared_skills = tmp_path / ".agents/skills"
    shared_skills.mkdir(parents=True)
    superpowers_link = shared_skills / "superpowers"
    superpowers_link.symlink_to(codex_skills)
    unrelated_target = tmp_path / "other-skills"
    unrelated_target.mkdir()
    unrelated_link = shared_skills / "keep"
    unrelated_link.symlink_to(unrelated_target)

    result = run_installer(tmp_path)

    assert result.returncode == 0, result.stderr
    assert codex_skills.is_dir()
    assert not superpowers_link.exists()
    assert not superpowers_link.is_symlink()
    assert unrelated_link.is_symlink()


def test_superpowers_symlink_to_other_target_is_preserved(tmp_path: Path) -> None:
    other_skills = tmp_path / "other-superpowers/skills"
    other_skills.mkdir(parents=True)
    shared_skills = tmp_path / ".agents/skills"
    shared_skills.mkdir(parents=True)
    superpowers_link = shared_skills / "superpowers"
    superpowers_link.symlink_to(other_skills)

    result = run_installer(tmp_path)

    assert result.returncode == 0, result.stderr
    assert superpowers_link.is_symlink()
    assert superpowers_link.resolve() == other_skills


def test_symlink_config_is_rejected_without_changing_link_or_target(tmp_path: Path) -> None:
    target = tmp_path / "real-config.toml"
    original = b'custom = "unchanged"\n'
    target.write_bytes(original)
    config = tmp_path / "config.toml"
    config.symlink_to(target.name)

    result = run_configure(config)

    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()
    assert config.is_symlink()
    assert os.readlink(config) == target.name
    assert target.read_bytes() == original
    assert artifacts(config) == []


def test_existing_config_rolls_back_bytes_mode_and_artifacts_on_failure(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.toml"
    original = b'unknown = "original"\n'
    config.write_bytes(original)
    config.chmod(0o604)

    result = run_configure(config, "upsert_table_key() { return 1; }")

    assert result.returncode != 0
    assert config.read_bytes() == original
    assert stat.S_IMODE(config.stat().st_mode) == 0o604
    assert artifacts(config) == []


def test_missing_config_rolls_back_to_absent_on_failure(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"

    result = run_configure(config, "upsert_table_key() { return 1; }")

    assert result.returncode != 0
    assert not config.exists()
    assert not config.is_symlink()
    assert artifacts(config) == []
