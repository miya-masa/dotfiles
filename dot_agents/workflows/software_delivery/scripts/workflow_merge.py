#!/usr/bin/env python3
"""The single, evidence-gated GitLab merge entry point."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


def _module(name: str):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("workflow_merge_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


state = _module("workflow_state")
evidence = _module("workflow_evidence")


class MergeError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def _json_call(argv, cwd):
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                shell=False, check=False)
    except OSError as exc:
        raise MergeError(f"E_GITLAB: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "GitLab API request failed"
        raise MergeError(f"E_GITLAB: {detail}")
    try:
        return json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        raise MergeError(f"E_GITLAB: invalid JSON response: {exc}") from exc


def _string(value, label):
    if not isinstance(value, str) or not value:
        raise MergeError(f"E_MERGE: invalid {label}")
    return value


def _mr_argv(host, project, iid, method="GET", payload=None):
    endpoint = f"projects/{project}/merge_requests/{iid}"
    argv = ["glab", "api", "--hostname", host, "--method", method]
    if payload is not None:
        argv += ["--field", f"sha={payload['sha']}", "--field", "should_remove_source_branch=true"]
        endpoint += "/merge"
    return argv + [endpoint]


def _project_argv(host, project):
    return ["glab", "api", "--hostname", host, "--method", "GET", f"projects/{project}"]


def _validate_project(value, project):
    if (not isinstance(value, dict) or type(value.get("id")) is not int
            or value["id"] != project
            or value.get("only_allow_merge_if_pipeline_succeeds") is not True
            or value.get("allow_merge_on_skipped_pipeline") is not False):
        raise MergeError(f"E_MERGE: project {project} requires matching id, only_allow_merge_if_pipeline_succeeds=true and allow_merge_on_skipped_pipeline=false")


def _identity(context, manifest):
    ci = manifest.get("ci")
    if not isinstance(ci, dict):
        raise MergeError("E_MERGE: fixed CI identity is required")
    host, project = ci.get("host"), ci.get("project_id")
    if not isinstance(host, str) or not host or type(project) is not int or project <= 0:
        raise MergeError("E_MERGE: invalid fixed CI identity")
    return host, project


def _validate_mr(mr, project, iid, sha, default_branch, source_branch, *, require_pipeline_success=False):
    if not isinstance(mr, dict) or type(mr.get("iid")) is not int or mr.get("iid") != iid:
        raise MergeError("E_MERGE: MR IID mismatch")
    if any(type(mr.get(key)) is not int or mr.get(key) != project
           for key in ("target_project_id", "source_project_id")):
        raise MergeError("E_MERGE: MR project identity or fork mismatch")
    if mr.get("target_branch") != default_branch or mr.get("source_branch") != source_branch:
        raise MergeError("E_MERGE: MR branch mismatch")
    if mr.get("sha") != sha:
        raise MergeError("E_MERGE: MR SHA mismatch")
    if mr.get("state") != "opened" or mr.get("draft") is True or mr.get("work_in_progress") is True:
        raise MergeError("E_MERGE: MR is not open and ready")
    pipeline = mr.get("head_pipeline")
    if (not isinstance(pipeline, dict) or pipeline.get("sha") != sha
            or type(pipeline.get("id")) is not int or pipeline["id"] <= 0):
        raise MergeError("E_MERGE: head pipeline is missing or stale")
    if require_pipeline_success and pipeline.get("status") != "success":
        raise MergeError("E_MERGE: head pipeline is not successful")
    return pipeline["id"]


def _candidate(context, sha):
    candidate = copy.deepcopy(context)
    candidate["state"] = dict(candidate["state"], phase="MR_READY")
    candidate["shipping"] = dict(candidate["shipping"], commit=sha)
    return candidate


def merge(context_path, iid, sha, authorize=False):
    if type(iid) is not int or iid <= 0:
        raise MergeError("E_MERGE: --mr must be a positive integer")
    if not isinstance(sha, str) or not (re.fullmatch(r"[0-9a-f]{40}", sha) or re.fullmatch(r"[0-9a-f]{64}", sha)):
        raise MergeError("E_MERGE: --sha must be a full hexadecimal commit SHA")
    try:
        context = state.load_context(context_path)
    except state.StateError as exc:
        raise MergeError(f"E_STATE: {exc}") from exc
    shipping_sha = context.get("shipping", {}).get("commit")
    if shipping_sha != sha:
        raise MergeError("E_MERGE: SHA differs from shipping.commit")
    try:
        manifest = evidence.load_contract(context_path, context)
        repo = evidence.repository(context)
    except evidence.EvidenceError as exc:
        raise MergeError(str(exc)) from exc
    host, project = _identity(context, manifest)
    source_branch = context.get("workspace", {}).get("branch")
    default_branch = context.get("identity", {}).get("default_branch")
    _string(source_branch, "workspace.branch")
    _string(default_branch, "identity.default_branch")
    _validate_project(_json_call(_project_argv(host, project), repo), project)
    mr = _json_call(_mr_argv(host, project, iid), repo)
    pipeline_id = _validate_mr(mr, project, iid, sha, default_branch, source_branch)

    # Refresh the fixed head pipeline through the existing immutable CI receipt path.
    try:
        evidence.collect_ci(context_path, pipeline_id)
        # collect_ci owns the directory lock while writing receipts. Reacquire
        # it before loading state and evaluating, so revocation cannot race the gate.
        with evidence._lock(Path(context_path).absolute().parent.resolve()):
            current = state.load_context(context_path)
            if current.get("shipping", {}).get("commit") != sha:
                raise MergeError("E_MERGE: shipping.commit changed during CI collection")
            # Preserve the identity used for collection while holding the gate lock
            # through the final remote check and the single merge request.
            current_manifest = evidence.load_contract(context_path, current)
            if (evidence.contract_hash(current_manifest) != evidence.contract_hash(manifest)
                    or current.get("workspace", {}).get("branch") != source_branch
                    or current.get("identity", {}).get("default_branch") != default_branch
                    or evidence.repository(current) != repo):
                raise MergeError("E_MERGE_RACE: local merge identity changed")
            candidate = _candidate(current, sha)
            result = evidence.evaluate_gates(context_path, current, candidate)
            if not authorize:
                return {"status": "checked", "sha": sha, "pipeline_id": pipeline_id, "gates": result.get("gates", {})}

            latest = _json_call(_mr_argv(host, project, iid), repo)
            try:
                latest_pipeline = _validate_mr(latest, project, iid, sha, default_branch, source_branch,
                                               require_pipeline_success=True)
                if latest_pipeline != pipeline_id:
                    raise MergeError("head pipeline changed")
            except MergeError as exc:
                raise MergeError(f"E_MERGE_RACE: {exc}") from exc
            merged = _json_call(_mr_argv(host, project, iid, "PUT", {"sha": sha}), repo)
            if (not isinstance(merged, dict) or merged.get("state") != "merged"
                    or type(merged.get("iid")) is not int or merged["iid"] != iid
                    or any(type(merged.get(key)) is not int or merged[key] != project
                           for key in ("source_project_id", "target_project_id"))
                    or merged.get("sha") != sha):
                raise MergeError("E_MERGE: merge response did not confirm merged identity")
            return {"status": "merged", "sha": sha, "pipeline_id": pipeline_id, "mr": merged}
    except (evidence.EvidenceError, state.StateError) as exc:
        raise MergeError(str(exc)) from exc



def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--mr", required=True, type=int)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--authorize", choices=["MERGE"])
    args = parser.parse_args(argv)
    try:
        result = merge(Path(args.context), args.mr, args.sha, args.authorize == "MERGE")
    except (MergeError, evidence.EvidenceError, state.StateError, OSError, ValueError, TypeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
