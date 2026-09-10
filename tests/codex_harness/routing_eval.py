#!/usr/bin/env python3
"""Deterministic quality-first evaluation for Codex harness routing changes."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import pty
import statistics
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CLASSES = {
    "clear_local",
    "normal_multi_file",
    "ambiguous_spec",
    "high_risk_protected_contract",
    "independent_parallel_exploration",
}
REQUIRED_RESPONSE = {
    "route",
    "tier",
    "cardinality",
    "lenses",
    "failure_route",
    "verdict",
    "detected_defect_ids",
    "active_ac_status",
    "approval_gate",
    "evidence_gate",
    "dispatches",
}


class RoutingEvalError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingEvalError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RoutingEvalError(f"expected object in {path}")
    return value


def validate_fixture(manifest_path: Path, oracle_path: Path, lock_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest, oracle, lock = _load(manifest_path), _load(oracle_path), _load(lock_path)
    lock_schema = lock.get("schema_version", 1)
    if lock_schema not in {1, 2}:
        raise RoutingEvalError(f"unsupported lock schema version: {lock_schema}")
    if manifest.get("schema_version", 1) != lock_schema:
        raise RoutingEvalError("manifest and lock schema versions differ")
    if sha256_file(manifest_path) != lock.get("manifest_sha256"):
        raise RoutingEvalError("manifest hash does not match lock")
    if sha256_file(oracle_path) != lock.get("oracle_sha256"):
        raise RoutingEvalError("oracle hash does not match lock")
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list) or {item.get("class") for item in scenarios if isinstance(item, dict)} != REQUIRED_CLASSES:
        raise RoutingEvalError("manifest must contain exactly five classes")
    if any(item.get("repetitions") != 3 for item in scenarios):
        raise RoutingEvalError("every scenario must have 3 repetitions")
    ids = [item.get("id") for item in scenarios]
    if len(ids) != len(set(ids)) or set(ids) != set(oracle.get("scenarios", {})):
        raise RoutingEvalError("manifest and oracle scenario IDs differ")
    if lock_schema == 2:
        baseline = lock.get("baseline")
        candidate = lock.get("candidate")
        if not isinstance(baseline, dict) or not isinstance(candidate, dict):
            raise RoutingEvalError("v2 lock must contain baseline and candidate pin sets")
        if not isinstance(baseline.get("base_commit"), str) or not baseline["base_commit"]:
            raise RoutingEvalError("v2 baseline pin set is missing base_commit")
        for variant, pins in (("baseline", baseline), ("candidate", candidate)):
            if not isinstance(pins.get("controller_pin"), dict) or not isinstance(pins.get("agent_pins"), dict):
                raise RoutingEvalError(f"v2 {variant} pin set is incomplete")
            defaults = pins.get("subagent_defaults")
            if variant == "candidate" and lock.get("suite_version") == "routing-eval-v3":
                if not isinstance(defaults, dict) or defaults.get("model") != "gpt-6-astra" or defaults.get("effort") != "high":
                    raise RoutingEvalError("v3 candidate subagent defaults are missing")
    return manifest, oracle, lock


def _instruction_paths(variant: str, scenario: dict[str, Any]) -> list[str]:
    """Return the instruction paths selected for one fixture variant."""
    variant_paths = scenario.get(f"{variant}_instruction_paths")
    if variant_paths is None:
        variant_paths = scenario.get("instruction_paths")
    if not isinstance(variant_paths, list) or not all(isinstance(path, str) for path in variant_paths):
        raise RoutingEvalError(f"invalid {variant} instruction paths")
    return variant_paths


def _instructions(variant: str, scenario: dict[str, Any], base_commit: str) -> str:
    chunks: list[str] = []
    for relative in _instruction_paths(variant, scenario):
        if variant == "baseline":
            result = subprocess.run(
                ["git", "show", f"{base_commit}:{relative}"], cwd=ROOT, text=True, capture_output=True, check=False
            )
            if result.returncode:
                raise RoutingEvalError(f"cannot read baseline instruction {relative}: {result.stderr.strip()}")
            content = result.stdout
        else:
            try:
                content = (ROOT / relative).read_text(encoding="utf-8")
            except OSError as exc:
                raise RoutingEvalError(f"cannot read candidate instruction {relative}: {exc}") from exc
        chunks.append(f"\n## {relative}\n{content}")
    return "".join(chunks)


def _variant_lock(lock: dict[str, Any], variant: str) -> dict[str, Any]:
    """Select a variant pin set while retaining the v1 flat-lock format."""
    if variant not in {"baseline", "candidate"}:
        raise RoutingEvalError("variant must be baseline or candidate")
    if not _is_v2(lock):
        return lock
    selected = lock.get(variant)
    if not isinstance(selected, dict):
        raise RoutingEvalError(f"missing {variant} pin set")
    return selected


def _is_v2(lock: dict[str, Any]) -> bool:
    return lock.get("schema_version", 1) == 2


def _pin_path(pin: dict[str, Any], role: str) -> Path:
    relative = pin.get("path")
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise RoutingEvalError(f"invalid agent pin path: {role}")
    return Path(relative)


def _pin_values(pin: dict[str, Any], role: str) -> tuple[str, str]:
    model, effort = pin.get("model"), pin.get("effort")
    if not isinstance(model, str) or not isinstance(effort, str):
        raise RoutingEvalError(f"invalid agent pin: {role}")
    return model, effort


def _check_agent_pins(
    lock: dict[str, Any], variant: str | None = None, *, extraction_dir: Path | None = None
) -> list[tuple[str, Path]]:
    variant = variant or "candidate"
    selected = _variant_lock(lock, variant)
    pins = selected.get("agent_pins")
    if not isinstance(pins, dict):
        raise RoutingEvalError(f"missing {variant} agent pins")
    base_commit = selected.get("base_commit", lock.get("base_commit"))
    if _is_v2(lock) and variant == "baseline" and (not isinstance(base_commit, str) or not base_commit):
        raise RoutingEvalError("baseline pin set is missing base_commit")
    agents: list[tuple[str, Path]] = []
    for role, raw_pin in pins.items():
        if not isinstance(role, str) or not isinstance(raw_pin, dict):
            raise RoutingEvalError(f"invalid agent pin: {role}")
        pin = raw_pin
        relative = _pin_path(pin, role)
        if pin.get("model") is None and pin.get("effort") is None:
            if "model" not in pin or "effort" not in pin or _subagent_defaults(lock, variant) is None:
                raise RoutingEvalError(f"unpinned agent requires explicit null pins and subagent defaults: {role}")
            expected_model = expected_effort = None
        elif pin.get("model") is None or pin.get("effort") is None:
            raise RoutingEvalError(f"agent pin mismatch: {role}")
        else:
            expected_model, expected_effort = _pin_values(pin, role)
        if _is_v2(lock) and variant == "baseline":
            result = subprocess.run(
                ["git", "show", f"{base_commit}:{relative.as_posix()}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                raise RoutingEvalError(f"cannot read baseline agent {role}: {result.stderr.strip()}")
            content = result.stdout
            if extraction_dir is None:
                raise RoutingEvalError("baseline agent extraction directory is required")
            path = extraction_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        else:
            path = ROOT / relative
            if not path.is_file():
                raise RoutingEvalError(f"missing agent config: {path}")
            content = path.read_text(encoding="utf-8")
        try:
            config = tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            raise RoutingEvalError(f"invalid agent config: {role}") from exc
        if expected_model is None:
            if "model" in config or "model_reasoning_effort" in config:
                raise RoutingEvalError(f"agent pin must be unpinned: {role}")
        elif config.get("model") != expected_model or config.get("model_reasoning_effort") != expected_effort:
            raise RoutingEvalError(f"agent pin mismatch: {role}")
        agents.append((role, path.resolve()))
    return agents


def _controller_pin(lock: dict[str, Any], variant: str) -> dict[str, str]:
    selected = _variant_lock(lock, variant)
    pin = selected.get("controller_pin")
    if not isinstance(pin, dict):
        raise RoutingEvalError(f"missing {variant} controller pin")
    model, effort = pin.get("model"), pin.get("effort")
    if not isinstance(model, str) or not isinstance(effort, str):
        raise RoutingEvalError(f"invalid {variant} controller pin")
    return {"model": model, "effort": effort}


def _record_model_effort(lock: dict[str, Any], variant: str, scenario: dict[str, Any]) -> dict[str, str]:
    if _is_v2(lock):
        return _controller_pin(lock, variant)
    value = scenario.get("model_effort")
    if not isinstance(value, dict) or not isinstance(value.get("model"), str) or not isinstance(value.get("effort"), str):
        raise RoutingEvalError(f"invalid scenario model/effort: {scenario.get('id')}")
    return {"model": value["model"], "effort": value["effort"]}

def _subagent_defaults(lock: dict[str, Any], variant: str) -> dict[str, str] | None:
    if not _is_v2(lock):
        return None
    defaults = _variant_lock(lock, variant).get("subagent_defaults")
    pins = _variant_lock(lock, variant).get("agent_pins", {})
    if any(isinstance(pin, dict) and pin.get("model") is None and pin.get("effort") is None for pin in pins.values()) and defaults is None:
        raise RoutingEvalError(f"{variant} subagent defaults are required for unpinned agents")
    if defaults is None:
        return None
    if not isinstance(defaults, dict) or not isinstance(defaults.get("model"), str) or not isinstance(defaults.get("effort"), str) or not defaults["model"] or defaults["effort"] not in {"low", "medium", "high", "xhigh", "max"}:
        raise RoutingEvalError(f"invalid {variant} subagent defaults")
    return {"model": defaults["model"], "effort": defaults["effort"]}


def _parse_events(stdout: str) -> tuple[dict[str, Any], dict[str, int], int, int, int]:
    response: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    calls = turns = retries = 0
    allowed = {"thread.started", "turn.started", "item.started", "item.updated", "item.completed", "turn.completed", "turn.failed", "error"}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RoutingEvalError("codex emitted invalid JSONL") from exc
        kind = event.get("type")
        if kind not in allowed:
            raise RoutingEvalError(f"unknown codex event: {kind}")
        if kind in {"turn.failed", "error"}:
            raise RoutingEvalError(f"codex reported {kind}")
        if kind == "turn.started":
            turns += 1
            if turns > 1:
                retries += 1
        if kind == "item.completed":
            item = event.get("item", {})
            if item.get("type") in {"tool_call", "command_execution", "mcp_tool_call"}:
                calls += 1
            if item.get("type") == "agent_message":
                try:
                    response = json.loads(item.get("text", ""))
                except json.JSONDecodeError as exc:
                    raise RoutingEvalError("final agent_message is not JSON") from exc
        if kind == "turn.completed":
            raw = event.get("usage")
            keys = {"input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"}
            if not isinstance(raw, dict) or not keys <= raw.keys() or not all(isinstance(raw[key], int) for key in keys):
                raise RoutingEvalError("turn.completed usage is missing or invalid")
            usage = {key: raw[key] for key in keys}
    if response is None or usage is None:
        raise RoutingEvalError("codex output lacks final response or usage")
    if not REQUIRED_RESPONSE <= response.keys():
        raise RoutingEvalError("agent response does not match result schema")
    calls += 1  # the top-level Codex invocation
    return response, usage, calls, turns, retries


def _run_driver(argv: list[str], *, env: dict[str, str], timeout: float) -> subprocess.CompletedProcess[str]:
    """Run through the login shell environment and keep stdin attached to a TTY."""
    master, slave = pty.openpty()
    command = ["zsh", "-lc", 'exec "$@"', "routing-eval", *argv]
    try:
        process = subprocess.Popen(
            command, cwd=ROOT, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env,
        )
        os.close(slave)
        slave = -1
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    finally:
        if slave >= 0:
            os.close(slave)
        os.close(master)


def run_evaluation(
    *, variant: str, manifest_path: Path, oracle_path: Path, lock_path: Path, output_path: Path,
    codex_executable: str = "codex", preflight: bool = True, environ: dict[str, str] | None = None,
    scenario_ids: list[str] | None = None,
) -> None:
    if variant not in {"baseline", "candidate"}:
        raise RoutingEvalError("variant must be baseline or candidate")
    manifest, _oracle, lock = validate_fixture(manifest_path, oracle_path, lock_path)
    controller_pin = _controller_pin(lock, variant)
    env = dict(os.environ if environ is None else environ)
    if preflight:
        version = subprocess.run([codex_executable, "--version"], text=True, capture_output=True, env=env, check=False)
        if version.returncode or version.stdout.strip() != lock["codex_version"]:
            raise RoutingEvalError("codex version mismatch")
        login = subprocess.run([codex_executable, "login", "status"], text=True, capture_output=True, env=env, check=False)
        if login.returncode:
            raise RoutingEvalError("codex login status failed")
    selected = [s for s in manifest["scenarios"] if scenario_ids is None or s["id"] in scenario_ids]
    if scenario_ids is not None and len(selected) != len(set(scenario_ids)):
        raise RoutingEvalError("unknown scenario ID")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="routing-eval-agents-") as agent_tmp:
        extraction_dir = Path(agent_tmp) if _is_v2(lock) and variant == "baseline" else None
        agents = _check_agent_pins(lock, variant, extraction_dir=extraction_dir)
        with output_path.open("w", encoding="utf-8") as stream:
            for scenario in selected:
                for repetition in range(1, scenario["repetitions"] + 1):
                    record: dict[str, Any] = {
                        "scenario_id": scenario["id"], "class": scenario["class"], "repetition": repetition,
                        "variant": variant, "status": "failed", "manifest_sha256": sha256_file(manifest_path),
                        "oracle_sha256": sha256_file(oracle_path), "model_effort": _record_model_effort(lock, variant, scenario),
                    }
                    defaults = _subagent_defaults(lock, variant)
                    if defaults is not None:
                        record["subagent_defaults"] = defaults
                    try:
                        base_commit = _variant_lock(lock, variant).get("base_commit", lock.get("base_commit", ""))
                        if variant == "baseline" and (not isinstance(base_commit, str) or not base_commit):
                            raise RoutingEvalError("missing base_commit")
                        content = _instructions(variant, scenario, base_commit)
                        instructions = ROOT / "tests/codex_harness/.routing-eval-instructions.md"
                        instructions.write_text(content, encoding="utf-8")
                        try:
                            argv = [codex_executable, "exec", "--ephemeral", "--json", "--ignore-user-config", "--ignore-rules", "--enable", "multi_agent", "-C", str(ROOT), "--sandbox", "read-only", "--model", controller_pin["model"], "-c", f'model_reasoning_effort="{controller_pin["effort"]}"', "-c", f'model_instructions_file="{instructions}"']
                            if defaults is not None:
                                argv.extend(["-c", f'agents.default_subagent_model="{defaults["model"]}"', "-c", f'agents.default_subagent_reasoning_effort="{defaults["effort"]}"'])
                            for role, path in agents:
                                argv.extend(["-c", f'agents.{role}.config_file="{path}"'])
                            argv.extend([
                                "--output-schema", str((ROOT / manifest["result_schema_path"]).resolve()),
                                scenario["input_packet"],
                            ])
                            started = time.monotonic_ns()
                            completed = _run_driver(argv, env=env, timeout=manifest["run_timeout_seconds"])
                            elapsed = time.monotonic_ns() - started
                        finally:
                            instructions.unlink(missing_ok=True)
                        if completed.returncode:
                            diagnostic = completed.stderr.strip() or completed.stdout.strip()
                            detail = diagnostic.splitlines()[-1] if diagnostic else "no diagnostic output"
                            raise RoutingEvalError(f"codex exited {completed.returncode}: {detail}")
                        response, usage, calls, turns, retries = _parse_events(completed.stdout)
                        total = usage["input_tokens"] + usage["output_tokens"]
                        record.update(response)
                        record.update(status="ok", tokens={**usage, "total_tokens": total}, wall_clock_ns=elapsed, calls=calls, turns=turns, retries=retries)
                    except (RoutingEvalError, subprocess.TimeoutExpired) as exc:
                        record["error"] = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else str(exc)
                        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                        stream.flush()
                        raise RoutingEvalError(record["error"]) from exc
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                    stream.flush()


def _read_records(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingEvalError(f"invalid evaluation file {path}: {exc}") from exc


def compare_evaluations(*, manifest_path: Path, oracle_path: Path, lock_path: Path, baseline_path: Path, candidate_path: Path, output_path: Path) -> dict[str, Any]:
    manifest, oracle, lock = validate_fixture(manifest_path, oracle_path, lock_path)
    baseline, candidate = _read_records(baseline_path), _read_records(candidate_path)
    quality_errors: list[str] = []
    scenarios = {item["id"]: item for item in manifest["scenarios"]}
    manifest_sha256 = sha256_file(manifest_path)
    oracle_sha256 = sha256_file(oracle_path)

    for variant, rows in (("baseline", baseline), ("candidate", candidate)):
        expected_records = Counter(
            (scenario["id"], scenario["class"], repetition, variant)
            for scenario in manifest["scenarios"]
            for repetition in range(1, scenario["repetitions"] + 1)
        )
        actual_records = Counter(
            (row.get("scenario_id"), row.get("class"), row.get("repetition"), row.get("variant"))
            for row in rows
        )
        if actual_records != expected_records:
            quality_errors.append(f"{variant} record identity mismatch")

        for row in rows:
            sid = row.get("scenario_id")
            scenario = scenarios.get(sid)
            expected = oracle.get("scenarios", {}).get(sid, {})
            defects = {
                item["id"]
                for item in expected.get("injected_defects", [])
                if item.get("severity") in {"Critical", "Important"}
            }
            if (
                row.get("status") != "ok"
                or row.get("verdict") != expected.get("expected_verdict")
                or not defects <= set(row.get("detected_defect_ids", []))
            ):
                quality_errors.append(f"{variant} quality failure: {sid}")
            if (
                row.get("approval_gate") != "satisfied"
                or row.get("evidence_gate") != "satisfied"
                or not row.get("active_ac_status")
            ):
                quality_errors.append(f"{variant} gate failure: {sid}")
            if scenario is None:
                quality_errors.append(f"{variant} unknown scenario: {sid}")
                continue
            expected_model_effort = _record_model_effort(lock, variant, scenario)
            if row.get("model_effort") != expected_model_effort:
                quality_errors.append(f"{variant} model/effort mismatch: {sid}")
            expected_defaults = _subagent_defaults(lock, variant)
            if row.get("subagent_defaults") != expected_defaults:
                quality_errors.append(f"{variant} subagent defaults mismatch: {sid}")
            if row.get("manifest_sha256") != manifest_sha256 or row.get("oracle_sha256") != oracle_sha256:
                quality_errors.append(f"{variant} fixture hash mismatch: {sid}")

    for row in candidate:
        sid = row.get("scenario_id")
        scenario = scenarios.get(sid)
        if scenario is None:
            continue
        # v3 checks the model's declared dispatch choices, not observed runtime settings.
        if "expected_dispatches" in scenario:
            actual = row.get("dispatches")
            expected_dispatches = scenario["expected_dispatches"]
            if not isinstance(actual, list) or sorted(json.dumps(item, sort_keys=True) for item in actual) != sorted(json.dumps(item, sort_keys=True) for item in expected_dispatches):
                quality_errors.append(f"dispatch selection mismatch: {sid}")
        route = scenario["expected"]
        for field in ("route", "tier", "cardinality", "failure_route"):
            if row.get(field) != route[field]:
                quality_errors.append(f"routing mismatch: {sid}.{field}")
        actual_lenses = set(row.get("lenses", []))
        if not set(route["lenses"]) <= actual_lenses or (not route["lenses"] and actual_lenses):
            quality_errors.append(f"routing mismatch: {sid}.lenses")
    report: dict[str, Any] = {"quality_gate": "FAIL" if quality_errors else "PASS", "quality_errors": quality_errors, "resource_gate": "NOT_EVALUATED"}
    if not quality_errors:
        direct_ids = {item["id"] for item in manifest["scenarios"] if item["direct_eligible"]}
        b = [row for row in baseline if row["scenario_id"] in direct_ids]
        c = [row for row in candidate if row["scenario_id"] in direct_ids]
        b_tokens, c_tokens = statistics.median(row["tokens"]["total_tokens"] for row in b), statistics.median(row["tokens"]["total_tokens"] for row in c)
        b_time, c_time = statistics.median(row["wall_clock_ns"] for row in b), statistics.median(row["wall_clock_ns"] for row in c)
        report.update(resource_gate="PASS" if c_tokens < b_tokens and c_time < b_time else "FAIL", baseline_median_tokens=b_tokens, candidate_median_tokens=c_tokens, baseline_median_wall_clock_ns=b_time, candidate_median_wall_clock_ns=c_time)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if quality_errors:
        raise RoutingEvalError("candidate failed quality gate")
    if report["resource_gate"] != "PASS":
        raise RoutingEvalError("candidate failed resource gate")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run", "compare"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--oracle", type=Path, required=True)
        command.add_argument("--lock", type=Path, required=True)
        if name == "run":
            command.add_argument("--variant", choices=("baseline", "candidate"), required=True)
            command.add_argument("--output", type=Path, required=True)
        if name == "compare":
            command.add_argument("--baseline", type=Path, required=True)
            command.add_argument("--candidate", type=Path, required=True)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate_fixture(args.manifest, args.oracle, args.lock)
        elif args.command == "run":
            run_evaluation(variant=args.variant, manifest_path=args.manifest, oracle_path=args.oracle, lock_path=args.lock, output_path=args.output)
        else:
            compare_evaluations(manifest_path=args.manifest, oracle_path=args.oracle, lock_path=args.lock, baseline_path=args.baseline, candidate_path=args.candidate, output_path=args.output)
    except RoutingEvalError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
