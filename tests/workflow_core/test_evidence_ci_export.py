from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys

import pytest

from tests.workflow_core.test_workflow_evidence import contract, module, approved, save, ref, ARTIFACT
from tests.workflow_core.test_evidence_gates import with_ci, gate, advance, rejected, grant_consent


@pytest.fixture
def ci(gate, tmp_path, monkeypatch):
    e, state, repo, cp, m, context = gate
    with_ci(e, cp, m)
    commit = context['identity']['base_commit']
    context['shipping']['commit'] = commit
    context['authorization']['shipping_authorized'] = True
    context['state']['phase'] = 'CI'
    cp.write_text(json.dumps(context))
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    data = tmp_path / 'api-data.json'
    trace = tmp_path / 'api-trace.jsonl'
    fake = bin_dir / 'glab'
    fake.write_text('#!' + sys.executable + '\n' + '''import json, os, sys
from pathlib import Path
assert 'GLAB_DEBUG_HTTP' not in os.environ
with Path(os.environ['FAKE_TRACE']).open('a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
data = json.loads(Path(os.environ['FAKE_DATA']).read_text())
kind = 'jobs' if '/jobs?' in sys.argv[-1] else 'pipeline'
print(json.dumps(data[kind]))
print('SECRET_MUST_NOT_BE_RECORDED', file=sys.stderr)
sys.exit(data.get(kind + '_rc', 0))
''')
    fake.chmod(0o755)
    monkeypatch.setenv('PATH', str(bin_dir) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('FAKE_DATA', str(data))
    monkeypatch.setenv('FAKE_TRACE', str(trace))
    monkeypatch.setenv('GLAB_DEBUG_HTTP', 'true')
    pipeline = dict(id=1, project_id=1, sha=commit, status='success')
    response = dict(pipeline=pipeline, jobs=[dict(id=10, name='required', status='success', pipeline=copy.deepcopy(pipeline))])
    data.write_text(json.dumps(response))
    return e, state, repo, cp, m, data, response, trace


@pytest.mark.parametrize('case', ['success', 'wrong_project', 'wrong_sha', 'wrong_pipeline', 'missing_job', 'latest_failed', 'manual', 'skipped', 'canceled', 'pipeline_failed', 'job_identity', 'page2_latest_failed', 'partial_api'])
def test_gitlab_requires_matching_pipeline_and_latest_required_jobs(ci, case):
    e, state, repo, cp, m, data, response, trace = ci
    if case == 'wrong_project': response['pipeline']['project_id'] = 2
    if case == 'wrong_sha': response['pipeline']['sha'] = 'f' * 40
    if case == 'wrong_pipeline': response['pipeline']['id'] = 2
    if case == 'missing_job': response['jobs'] = []
    if case in ('latest_failed', 'page2_latest_failed'):
        if case == 'page2_latest_failed':
            response['jobs'].extend(dict(id=i, name=f'other-{i}', status='success', pipeline=response['pipeline']) for i in range(11, 111))
        response['jobs'].append(dict(id=200, name='required', status='failed', pipeline=response['pipeline']))
    if case in ('manual', 'skipped', 'canceled'): response['jobs'][0]['status'] = case
    if case == 'pipeline_failed': response['pipeline']['status'] = 'failed'
    if case == 'job_identity': response['jobs'][0]['pipeline']['id'] = 3
    if case == 'partial_api': response['jobs_rc'] = 1
    data.write_text(json.dumps(response))
    receipt = e.collect_ci(cp, 1)[0]
    assert receipt['results'][0]['status'] == ('passed' if case == 'success' else 'failed')
    calls = [json.loads(line) for line in trace.read_text().splitlines()]
    assert calls == [
        [
            'api', '--hostname', 'git.example.invalid', '--method', 'GET',
            'projects/1/pipelines/1',
        ],
        [
            'api', '--hostname', 'git.example.invalid', '--method', 'GET',
            '--paginate', '--output', 'json',
            'projects/1/pipelines/1/jobs?include_retried=true&per_page=100',
        ],
    ]
    directory = cp.parent / 'evidence' / 'runs' / receipt['run_id']
    assert all(b'SECRET_MUST_NOT_BE_RECORDED' not in p.read_bytes() for p in directory.iterdir())
    if case == 'success':
        assert advance(state, cp, 'MR_READY')['execution']['gates']['local_verification']['ci_pending'] is False
    else:
        rejected(state, cp, 'MR_READY', 'E_CI', {'execution': {'gates': {'local_verification': 'passed'}}})


def test_ci_latest_failure_raw_integrity_and_cli(ci):
    e, state, repo, cp, m, data, response, trace = ci
    command = [sys.executable, str(ARTIFACT), 'evidence-ci', '--context', str(cp), '--pipeline-id', '1']
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    receipt = json.loads(proc.stdout)[0]
    directory = cp.parent / 'evidence' / 'runs' / receipt['run_id']
    original = (directory / 'jobs.json').read_bytes()
    (directory / 'jobs.json').write_text('[]')
    rejected(state, cp, 'MR_READY', 'E_EVIDENCE_HASH')
    (directory / 'jobs.json').write_bytes(original)
    response['jobs_rc'] = 1
    data.write_text(json.dumps(response))
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 1
    rejected(state, cp, 'MR_READY', 'E_CI')
    response['jobs_rc'] = 0
    data.write_text(json.dumps(response))
    e.collect_ci(cp, 1)
    grant_consent(e, state, cp)
    advance(state, cp, 'MR_READY')
    assert subprocess.run(command[:-1] + ['https://arbitrary.invalid'], capture_output=True).returncode != 0


def test_ci_input_change_rejects_check_gates_and_transition(ci):
    e, state, repo, cp, m, data, response, trace = ci
    remote = m['checks'][1]
    ci_input = cp.parent / 'ci-input.txt'
    ci_input.write_text('ci input')
    remote['inputs'] = [ref('workflow', 'ci-input.txt', cp.parent)]
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    e.collect_ci(cp, 1)
    ci_input.write_text('changed after CI collection')

    before = cp.read_bytes()
    revision = json.loads(before)['state']['artifact_revision']
    assert state.main(['check-gates', '--context', str(cp), '--to', 'MR_READY']) == 1
    assert cp.read_bytes() == before
    assert state.load_context(cp)['state']['artifact_revision'] == revision
    rejected(state, cp, 'MR_READY', 'E_EVIDENCE_HASH')
    assert state.load_context(cp)['state']['artifact_revision'] == revision


@pytest.mark.parametrize('tamper', ['none', 'raw', 'receipt', 'start', 'oracle', 'review', 'input_manifest', 'missing'])
def test_export_verifies_after_relocation_and_detects_missing_or_changed_files(ci, tmp_path, tamper):
    e, state, repo, cp, m, data, response, trace = ci
    m['active'][0]['oracle'] = dict(ref('repo', 'input.txt', repo), locator='fixed input')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    receipt = e.collect_ci(cp, 1)[0]
    bundle = tmp_path / 'bundle'
    proc = subprocess.run([sys.executable, str(ARTIFACT), 'evidence-export', '--context', str(cp), '--output', str(bundle)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    relocated = tmp_path / 'relocated'
    shutil.copytree(bundle, relocated)
    shutil.rmtree(bundle)
    shutil.rmtree(cp.parent)
    shutil.rmtree(repo)
    run = relocated / 'workflow' / 'evidence' / 'runs' / receipt['run_id']
    targets = dict(raw=run / 'jobs.json', receipt=run / 'receipt.json', start=run / 'start.json', oracle=relocated / 'repo' / 'input.txt', review=relocated / 'workflow' / 'review.md', input_manifest=run / 'inputs.json', missing=run / 'receipt.json')
    if tamper == 'none':
        assert e.validate_export(relocated)['manifest'] == m
    else:
        if tamper == 'missing': targets[tamper].unlink()
        else: targets[tamper].write_text('tampered')
        with pytest.raises(e.EvidenceError): e.validate_export(relocated)


def test_export_rejects_latest_failed_and_unfinished_without_fallback(ci, tmp_path):
    e, state, repo, cp, m, data, response, trace = ci
    e.collect_ci(cp, 1)
    response['jobs'][0]['status'] = 'failed'
    data.write_text(json.dumps(response))
    receipt = e.collect_ci(cp, 1)[0]
    output = tmp_path / 'failed-export'
    with pytest.raises(e.EvidenceError, match='E_CI'):
        e.export_evidence(cp, output)
    assert not output.exists()
    directory = cp.parent / 'evidence' / 'runs' / receipt['run_id']
    start = e._json(directory / 'start.json')
    assert e.validate_receipt(cp.parent, m, m['checks'][1], directory, start, require_pass=False) == receipt
    (directory / 'receipt.json').unlink()
    unfinished = tmp_path / 'unfinished-export'
    with pytest.raises(e.EvidenceError): e.export_evidence(cp, unfinished)
    # The selected latest start is retained for diagnosis; older success is not used.
    assert (unfinished / 'workflow' / 'evidence' / 'runs' / receipt['run_id'] / 'start.json').is_file()
    assert len(list((unfinished / 'workflow' / 'evidence' / 'runs').iterdir())) == 2


def test_export_keeps_input_change_failure_and_api_interruption(ci, tmp_path, monkeypatch):
    e, state, repo, cp, m, data, response, trace = ci
    # This fixed command fails the before/after input check despite exit zero.
    m['checks'][0]['argv'] = [sys.executable, '-c', "from pathlib import Path; Path('../input.txt').write_text('changed'); print('fixed')"]
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)
    failed = e.run_check(cp, 'command-check')
    assert failed['results'][0]['status'] == 'failed'
    # Restore the live oracle/input so collection can continue at the same snapshot.
    (repo / 'input.txt').write_text('input')
    e.collect_ci(cp, 1)
    with pytest.raises(e.EvidenceError, match='E_ATTEMPT'):
        e.export_evidence(cp, tmp_path / 'changed-input-export')
    directory = cp.parent / 'evidence' / 'runs' / failed['run_id']
    assert e.validate_receipt(cp.parent, m, m['checks'][0], directory, e._json(directory / 'start.json'), require_pass=False) == failed
    original_run = e.subprocess.run
    def interrupt(argv, **kwargs):
        if argv[0] == 'glab': raise KeyboardInterrupt()
        return original_run(argv, **kwargs)
    monkeypatch.setattr(e.subprocess, 'run', interrupt)
    with pytest.raises(KeyboardInterrupt): e.collect_ci(cp, 1)
    directory, start = e.latest_start(cp, m, 'remote', m['review']['snapshot_id'])
    assert not (directory / 'receipt.json').exists()
    with pytest.raises(e.EvidenceError):
        e.validate_ci_receipt(cp.parent, m, m['checks'][1], directory, start, response['pipeline']['sha'])
