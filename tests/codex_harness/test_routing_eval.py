from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import routing_eval  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests/codex_harness/fixtures/routing_eval/v1"
V3_FIXTURE_ROOT = ROOT / "tests/codex_harness/fixtures/routing_eval/v3"


def _fixture_args(fixture_root: Path = FIXTURE_ROOT, oracle_root: Path = FIXTURE_ROOT) -> tuple[Path, Path, Path]:
    return (
        fixture_root / "manifest.json",
        oracle_root / "oracle.json",
        fixture_root / "lock.json",
    )


def _copy_fixture(tmp_path: Path, *, version: int = 1) -> tuple[Path, Path, Path]:
    fixture_root = V3_FIXTURE_ROOT if version == 2 else FIXTURE_ROOT
    paths = _fixture_args(fixture_root, FIXTURE_ROOT if version == 2 else fixture_root)
    copied = []
    for path in paths:
        target = tmp_path / path.name
        target.write_bytes(path.read_bytes())
        copied.append(target)
    return tuple(copied)  # type: ignore[return-value]


def _write_fake_codex(tmp_path: Path, mode: str = "ok", version: str = "codex-cli 0.151.0") -> Path:
    script = tmp_path / "fake-codex.py"
    script.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
import time

mode = os.environ.get("FAKE_CODEX_MODE", "ok")
if sys.argv[1:2] == ["--version"]:
    print(__VERSION__)
    raise SystemExit(0)
if sys.argv[1:3] == ["login", "status"]:
    print("logged in")
    raise SystemExit(0)
if mode == "timeout":
    time.sleep(5)
    raise SystemExit(0)
if mode == "nonzero":
    print(json.dumps({"type": "turn.started"}))
    raise SystemExit(7)
packet = sys.argv[-1]
log = os.environ.get("FAKE_CODEX_LOG")
if log:
    with open(log, "a", encoding="utf-8") as stream:
        json.dump({"argv": sys.argv[1:], "packet": packet}, stream)
        stream.write("\\n")
if mode == "missing_usage":
    events = [
        {"type": "thread.started", "thread_id": "fake"},
        {"type": "turn.started", "turn_id": "fake"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
        {"type": "turn.completed"},
    ]
elif mode == "schema":
    events = [
        {"type": "thread.started", "thread_id": "fake"},
        {"type": "turn.started", "turn_id": "fake"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
        {"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_output_tokens": 0}},
    ]
else:
    events = [
        {"type": "thread.started", "thread_id": "fake"},
        {"type": "turn.started", "turn_id": "fake"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({
            "route": "DIRECT",
            "tier": "minor",
            "cardinality": 0,
            "lenses": [],
            "failure_route": "controller_self_check",
            "verdict": "BLOCKED",
            "detected_defect_ids": ["DEF-CLEAR-001"],
            "active_ac_status": {"AC8": "pass"},
            "approval_gate": "satisfied",
            "evidence_gate": "satisfied",
            "dispatches": [],
        })}},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 4, "reasoning_output_tokens": 3}},
    ]
for event in events:
    print(json.dumps(event))
""".replace("__VERSION__", repr(version)),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(ROOT / "tests/codex_harness/routing_eval.py"), *args]
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=env, check=False)


def _write_records(
    path: Path,
    *,
    variant: str,
    tokens: int = 100,
    wrong: str | None = None,
    fixture_root: Path = FIXTURE_ROOT,
    oracle_root: Path = FIXTURE_ROOT,
) -> None:
    manifest = json.loads((fixture_root / "manifest.json").read_text(encoding="utf-8"))
    oracle = json.loads((oracle_root / "oracle.json").read_text(encoding="utf-8"))
    lock = json.loads((fixture_root / "lock.json").read_text(encoding="utf-8"))
    rows = []
    for scenario in manifest["scenarios"]:
        sid = scenario["id"]
        expected = scenario["expected"]
        for repetition in range(1, scenario["repetitions"] + 1):
            defect_ids = [item["id"] for item in oracle["scenarios"][sid]["injected_defects"]]
            verdict = oracle["scenarios"][sid]["expected_verdict"]
            if sid == wrong:
                defect_ids = []
                verdict = "APPROVED"
            row = {
                    "scenario_id": sid,
                    "class": scenario["class"],
                    "repetition": repetition,
                    "variant": variant,
                    "status": "ok",
                    "route": expected["route"],
                    "tier": expected["tier"],
                    "cardinality": expected["cardinality"],
                    "lenses": expected["lenses"],
                    "failure_route": expected["failure_route"],
                    "verdict": verdict,
                    "detected_defect_ids": defect_ids,
                    "active_ac_status": {"AC8": "pass"},
                    "approval_gate": "satisfied",
                    "evidence_gate": "satisfied",
                    "dispatches": scenario.get("expected_dispatches", []),
                    "model_effort": (
                        lock[variant]["controller_pin"] if lock.get("schema_version") == 2 else scenario["model_effort"]
                    ),
                    "tokens": {
                        "input_tokens": tokens // 2,
                        "cached_input_tokens": 0,
                        "output_tokens": tokens // 2,
                        "reasoning_output_tokens": 0,
                        "total_tokens": tokens,
                    },
                    "wall_clock_ns": tokens * 1000,
                    "calls": 1,
                    "turns": 1,
                    "retries": 0,
                    "manifest_sha256": routing_eval.sha256_file(fixture_root / "manifest.json"),
                    "oracle_sha256": routing_eval.sha256_file(oracle_root / "oracle.json"),
                }
            defaults = lock.get(variant, {}).get("subagent_defaults")
            if defaults is not None:
                row["subagent_defaults"] = defaults
            rows.append(row)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_validate_rejects_manifest_or_oracle_hash_mismatch(tmp_path: Path) -> None:
    manifest, oracle, lock = _copy_fixture(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["suite_version"] = "tampered"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(routing_eval.RoutingEvalError, match="manifest.*hash"):
        routing_eval.validate_fixture(manifest, oracle, lock)


def test_run_requires_five_classes_and_three_repetitions(tmp_path: Path) -> None:
    manifest, oracle, lock = _copy_fixture(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["scenarios"] = data["scenarios"][:-1]
    manifest.write_text(json.dumps(data), encoding="utf-8")
    lock_data = json.loads(lock.read_text(encoding="utf-8"))
    lock_data["manifest_sha256"] = routing_eval.sha256_file(manifest)
    lock.write_text(json.dumps(lock_data), encoding="utf-8")
    fake = _write_fake_codex(tmp_path)

    with pytest.raises(routing_eval.RoutingEvalError, match="five classes|5 classes"):
        routing_eval.run_evaluation(
            variant="candidate",
            manifest_path=manifest,
            oracle_path=oracle,
            lock_path=lock,
            output_path=tmp_path / "result.jsonl",
            codex_executable=str(fake),
            preflight=False,
        )


def test_compare_enforces_quality_before_resource_improvement(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_records(baseline, variant="baseline", tokens=100)
    _write_records(candidate, variant="candidate", tokens=50, wrong="ambiguous-spec")
    report = tmp_path / "comparison.json"

    with pytest.raises(routing_eval.RoutingEvalError, match="quality"):
        routing_eval.compare_evaluations(
            manifest_path=FIXTURE_ROOT / "manifest.json",
            oracle_path=FIXTURE_ROOT / "oracle.json",
            lock_path=FIXTURE_ROOT / "lock.json",
            baseline_path=baseline,
            candidate_path=candidate,
            output_path=report,
        )
    written = json.loads(report.read_text(encoding="utf-8"))
    assert written["quality_gate"] == "FAIL"
    assert written["resource_gate"] == "NOT_EVALUATED"


@pytest.mark.parametrize("variant", ["baseline", "candidate"])
def test_compare_rejects_missing_record_replaced_by_duplicate(tmp_path: Path, variant: str) -> None:
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_records(baseline, variant="baseline", tokens=100)
    _write_records(candidate, variant="candidate", tokens=50)
    selected = baseline if variant == "baseline" else candidate
    rows = [json.loads(line) for line in selected.read_text(encoding="utf-8").splitlines()]
    rows[-1] = dict(rows[0])
    selected.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    report = tmp_path / "comparison.json"

    with pytest.raises(routing_eval.RoutingEvalError, match="quality"):
        routing_eval.compare_evaluations(
            manifest_path=FIXTURE_ROOT / "manifest.json",
            oracle_path=FIXTURE_ROOT / "oracle.json",
            lock_path=FIXTURE_ROOT / "lock.json",
            baseline_path=baseline,
            candidate_path=candidate,
            output_path=report,
        )
    written = json.loads(report.read_text(encoding="utf-8"))
    assert written["quality_gate"] == "FAIL"
    assert written["resource_gate"] == "NOT_EVALUATED"
    assert f"{variant} record identity mismatch" in written["quality_errors"]


def test_run_selects_base_commit_or_worktree_instructions_and_parses_codex_jsonl(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path, version="codex-cli 0.153.4")
    log = tmp_path / "driver.jsonl"
    env = {**os.environ, "FAKE_CODEX_LOG": str(log)}
    output_baseline = tmp_path / "baseline.jsonl"
    output_candidate = tmp_path / "candidate.jsonl"
    manifest, oracle, lock = _fixture_args(V3_FIXTURE_ROOT, FIXTURE_ROOT)
    lock_before = lock.read_bytes()

    routing_eval.run_evaluation(
        variant="baseline",
        manifest_path=manifest,
        oracle_path=oracle,
        lock_path=lock,
        output_path=output_baseline,
        codex_executable=str(fake),
        preflight=True,
        environ=env,
        scenario_ids=["clear-local"],
    )
    routing_eval.run_evaluation(
        variant="candidate",
        manifest_path=manifest,
        oracle_path=oracle,
        lock_path=lock,
        output_path=output_candidate,
        codex_executable=str(fake),
        preflight=True,
        environ=env,
        scenario_ids=["clear-local"],
    )

    records = [json.loads(line) for line in output_candidate.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 3
    assert records[0]["tokens"]["input_tokens"] == 10
    assert records[0]["tokens"]["cached_input_tokens"] == 2
    assert records[0]["calls"] == 1
    assert records[0]["turns"] == 1
    assert records[0]["retries"] == 0
    assert records[0]["route"] == "DIRECT"
    assert records[0]["model_effort"] == {"model": "gpt-6-astra", "effort": "low"}
    assert records[0]["subagent_defaults"] == {"model": "gpt-6-astra", "effort": "high"}
    baseline_records = [json.loads(line) for line in output_baseline.read_text(encoding="utf-8").splitlines()]
    assert baseline_records[0]["model_effort"] == {"model": "gpt-6-astra", "effort": "low"}
    assert lock.read_bytes() == lock_before
    checked_in_lock = json.loads(lock.read_text(encoding="utf-8"))
    assert checked_in_lock["baseline"]["agent_pins"]["explorer"]["effort"] == "low"
    assert checked_in_lock["candidate"]["agent_pins"]["explorer"]["model"] is None
    logged = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    normal_calls = [item for item in logged if "--output-schema" in item["argv"]]
    assert len(normal_calls) == 6
    for item in normal_calls:
        assert item["packet"]
        instruction_arg = next(arg for arg in item["argv"] if arg.startswith("model_instructions_file="))
        assert instruction_arg.startswith("model_instructions_file=")
        assert "--sandbox" in item["argv"]
        assert "read-only" in item["argv"]
        assert "--ignore-user-config" in item["argv"]
        assert "--ignore-rules" in item["argv"]
    baseline_call = next(item for item in normal_calls if 'model_reasoning_effort="low"' in item["argv"])
    candidate_call = next(item for item in normal_calls if 'agents.default_subagent_model="gpt-6-astra"' in item["argv"])
    assert baseline_call["argv"][baseline_call["argv"].index("--model") + 1] == "gpt-6-astra"
    assert candidate_call["argv"][candidate_call["argv"].index("--model") + 1] == "gpt-6-astra"
    baseline_explorer = next(arg for arg in baseline_call["argv"] if arg.startswith("agents.explorer.config_file="))
    candidate_explorer = next(arg for arg in candidate_call["argv"] if arg.startswith("agents.explorer.config_file="))
    assert "routing-eval-agents-" in baseline_explorer
    assert "routing-eval-agents-" not in candidate_explorer


def test_v3_run_rejects_candidate_pin_mismatch(tmp_path: Path) -> None:
    fake = _write_fake_codex(tmp_path, version="codex-cli 0.153.4")
    manifest, oracle, lock = _copy_fixture(tmp_path, version=2)
    lock_data = json.loads(lock.read_text(encoding="utf-8"))
    lock_data["candidate"]["agent_pins"]["explorer"]["effort"] = "max"
    lock.write_text(json.dumps(lock_data), encoding="utf-8")

    with pytest.raises(routing_eval.RoutingEvalError, match="agent pin mismatch: explorer"):
        routing_eval.run_evaluation(
            variant="candidate",
            manifest_path=manifest,
            oracle_path=oracle,
            lock_path=lock,
            output_path=tmp_path / "candidate.jsonl",
            codex_executable=str(fake),
            preflight=False,
            scenario_ids=["clear-local"],
        )


def test_v3_compare_checks_variant_controller_pin_in_records(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_records(baseline, variant="baseline", tokens=100, fixture_root=V3_FIXTURE_ROOT, oracle_root=FIXTURE_ROOT)
    _write_records(candidate, variant="candidate", tokens=50, fixture_root=V3_FIXTURE_ROOT, oracle_root=FIXTURE_ROOT)
    report = tmp_path / "comparison.json"

    result = routing_eval.compare_evaluations(
        manifest_path=V3_FIXTURE_ROOT / "manifest.json",
        oracle_path=FIXTURE_ROOT / "oracle.json",
        lock_path=V3_FIXTURE_ROOT / "lock.json",
        baseline_path=baseline,
        candidate_path=candidate,
        output_path=report,
    )
    assert result["quality_gate"] == "PASS"
    assert result["resource_gate"] == "PASS"

    rows = [json.loads(line) for line in candidate.read_text(encoding="utf-8").splitlines()]
    rows[0]["model_effort"] = {"model": "gpt-5.6-sol", "effort": "medium"}
    candidate.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(routing_eval.RoutingEvalError, match="quality"):
        routing_eval.compare_evaluations(
            manifest_path=V3_FIXTURE_ROOT / "manifest.json",
            oracle_path=FIXTURE_ROOT / "oracle.json",
            lock_path=V3_FIXTURE_ROOT / "lock.json",
            baseline_path=baseline,
            candidate_path=candidate,
            output_path=report,
        )
    written = json.loads(report.read_text(encoding="utf-8"))
    assert "candidate model/effort mismatch: clear-local" in written["quality_errors"]


@pytest.mark.parametrize("mode", ["missing_usage", "schema", "nonzero", "timeout"])
def test_run_fails_on_missing_usage_schema_mismatch_nonzero_exit_or_timeout(
    tmp_path: Path, mode: str
) -> None:
    fake = _write_fake_codex(tmp_path, mode=mode, version="codex-cli 0.153.4")
    output = tmp_path / f"{mode}.jsonl"
    manifest, oracle, lock = _copy_fixture(tmp_path, version=2)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["run_timeout_seconds"] = 0.1
    local_manifest = tmp_path / "manifest.json"
    local_manifest.write_text(json.dumps(data), encoding="utf-8")
    local_lock = tmp_path / "lock.json"
    lock_data = json.loads(lock.read_text(encoding="utf-8"))
    lock_data["manifest_sha256"] = routing_eval.sha256_file(local_manifest)
    local_lock.write_text(json.dumps(lock_data), encoding="utf-8")

    env = {**os.environ, "FAKE_CODEX_MODE": mode}
    with pytest.raises(routing_eval.RoutingEvalError):
        routing_eval.run_evaluation(
            variant="candidate",
            manifest_path=local_manifest,
            oracle_path=oracle,
            lock_path=local_lock,
            output_path=output,
            codex_executable=str(fake),
            preflight=False,
            environ=env,
            scenario_ids=["clear-local"],
        )
    assert output.is_file()
    failure = json.loads(output.read_text(encoding="utf-8").splitlines()[-1])
    assert failure["status"] == "failed"


@pytest.mark.parametrize("version", [1, 2])
def test_historical_compare_remains_compatible(tmp_path: Path, version: int) -> None:
    fixture = FIXTURE_ROOT.parent / f"v{version}"
    baseline, candidate = tmp_path / "baseline.jsonl", tmp_path / "candidate.jsonl"
    for path, variant in ((baseline, "baseline"), (candidate, "candidate")):
        _write_records(path, variant=variant, tokens=100 if variant == "baseline" else 50, fixture_root=fixture)
    result = routing_eval.compare_evaluations(
        manifest_path=fixture / "manifest.json", oracle_path=FIXTURE_ROOT / "oracle.json",
        lock_path=fixture / "lock.json", baseline_path=baseline, candidate_path=candidate,
        output_path=tmp_path / "report.json",
    )
    assert result["quality_gate"] == "PASS"


def test_v3_rejects_missing_defaults(tmp_path: Path) -> None:
    manifest, oracle, lock = _copy_fixture(tmp_path, version=2)
    data = json.loads(lock.read_text())
    del data["candidate"]["subagent_defaults"]
    lock.write_text(json.dumps(data))
    with pytest.raises(routing_eval.RoutingEvalError, match="defaults"):
        routing_eval.validate_fixture(manifest, oracle, lock)
    # Nullable pins also require defaults without the v3 suite marker.
    data.pop("suite_version")
    with pytest.raises(routing_eval.RoutingEvalError, match="defaults"):
        routing_eval._check_agent_pins(data, "candidate")


@pytest.mark.parametrize("key,value", [("model", '"gpt-5.6-luna"'), ("model_reasoning_effort", '"low"')])
def test_v3_rejects_a_pin_reintroduced_in_actual_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, value: str) -> None:
    data = json.loads((V3_FIXTURE_ROOT / "lock.json").read_text())
    for pin in data["candidate"]["agent_pins"].values():
        target = tmp_path / pin["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / pin["path"]).read_bytes())
    explorer = tmp_path / data["candidate"]["agent_pins"]["explorer"]["path"]
    explorer.write_text(f"{key} = {value}\n" + explorer.read_text())
    monkeypatch.setattr(routing_eval, "ROOT", tmp_path)
    with pytest.raises(routing_eval.RoutingEvalError, match="must be unpinned"):
        routing_eval._check_agent_pins(data, "candidate")


@pytest.mark.parametrize("defaults", [None, {"model": "gpt-6-astra", "effort": "low"}])
def test_v3_compare_rejects_missing_or_mismatched_defaults(tmp_path: Path, defaults: dict | None) -> None:
    baseline, candidate = tmp_path / "baseline.jsonl", tmp_path / "candidate.jsonl"
    for path, variant in ((baseline, "baseline"), (candidate, "candidate")):
        _write_records(path, variant=variant, fixture_root=V3_FIXTURE_ROOT)
    rows = [json.loads(line) for line in candidate.read_text().splitlines()]
    rows[0].pop("subagent_defaults")
    if defaults is not None:
        rows[0]["subagent_defaults"] = defaults
    candidate.write_text("".join(json.dumps(row) + "\n" for row in rows))
    report = tmp_path / "report.json"
    with pytest.raises(routing_eval.RoutingEvalError, match="quality"):
        routing_eval.compare_evaluations(
            manifest_path=V3_FIXTURE_ROOT / "manifest.json", oracle_path=FIXTURE_ROOT / "oracle.json",
            lock_path=V3_FIXTURE_ROOT / "lock.json", baseline_path=baseline, candidate_path=candidate,
            output_path=report,
        )
    assert any("subagent defaults mismatch" in error for error in json.loads(report.read_text())["quality_errors"])


@pytest.mark.parametrize("case", ["missing_model", "missing_effort", "expensive_worker", "cheap_reviewer"])
def test_v3_compare_rejects_wrong_explicit_dispatch_selection(tmp_path: Path, case: str) -> None:
    baseline, candidate = tmp_path / "baseline.jsonl", tmp_path / "candidate.jsonl"
    for path, variant in ((baseline, "baseline"), (candidate, "candidate")):
        _write_records(path, variant=variant, fixture_root=V3_FIXTURE_ROOT)
    rows = [json.loads(line) for line in candidate.read_text().splitlines()]
    normal = next(row for row in rows if row["scenario_id"] == "normal-multi-file")
    worker, reviewer = normal["dispatches"]
    if case == "missing_model":
        worker.pop("model")
    elif case == "missing_effort":
        worker.pop("reasoning_effort")
    elif case == "expensive_worker":
        worker.update(model="gpt-6-astra", reasoning_effort="high")
    else:
        reviewer.update(model="gpt-5.6-luna", reasoning_effort="low")
    candidate.write_text("".join(json.dumps(row) + "\n" for row in rows))
    report = tmp_path / "report.json"
    with pytest.raises(routing_eval.RoutingEvalError, match="quality"):
        routing_eval.compare_evaluations(
            manifest_path=V3_FIXTURE_ROOT / "manifest.json", oracle_path=FIXTURE_ROOT / "oracle.json",
            lock_path=V3_FIXTURE_ROOT / "lock.json", baseline_path=baseline, candidate_path=candidate,
            output_path=report,
        )
    assert "dispatch selection mismatch: normal-multi-file" in json.loads(report.read_text())["quality_errors"]
