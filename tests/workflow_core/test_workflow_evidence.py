from __future__ import annotations

import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'dot_agents/workflows/software_delivery/scripts/workflow_evidence.py'
ARTIFACT = EVIDENCE.with_name('workflow_artifact.py')


def module():
    spec = importlib.util.spec_from_file_location('evidence_test', EVIDENCE)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def ref(root, path, base):
    return dict(root=root, path=path, sha256=hashlib.sha256((base / path).read_bytes()).hexdigest())


def save(cpath, manifest):
    (cpath.parent / 'evidence.json').write_text(json.dumps(manifest))


@pytest.fixture
def contract(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    workflow = tmp_path / 'workflow'
    workflow.mkdir()
    (repo / 'input.txt').write_text('input')
    (repo / 'sub').mkdir()
    (repo / 'sub' / 'runner.py').write_text("print('fixed')\n")
    subprocess.run(['git', 'init', '-q', repo], check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    (workflow / 'spec.md').write_text('| AC ID | Lifecycle | Criterion |\n|---|---|---|\n| AC1 | ACTIVE | command works |\n| AC3 | ACTIVE | exact evidence |\n| AC2 | RETIRED | old |\n')
    for name in ('plan.md', 'task.md', 'review.md'):
        (workflow / name).write_text(name)
    check = dict(id='command-check', kind='command', argv=[sys.executable, 'runner.py'], cwd='sub', inputs=[ref('repo', 'input.txt', repo)], targets=[], expected_exit=0, assertions=[dict(stream='stdout', op='equals', value='fixed\n')])
    m = dict(version=1, workflow_id='fixture', source=ref('workflow', 'spec.md', workflow), allowlist=dict(version=1, paths=['input.txt', 'sub/runner.py']), active=[dict(id='AC1', oracle=dict(ref('workflow', 'spec.md', workflow), locator='AC1'), plan=ref('workflow', 'plan.md', workflow), task=ref('workflow', 'task.md', workflow), checks=['command-check'])], retired=[dict(id='AC2', reason='old')], checks=[check], review=None, ci=None)
    m['active'].append(dict(m['active'][0], id='AC3'))
    cpath = workflow / 'context.json'
    cpath.write_text(json.dumps(dict(identity=dict(workflow_id='fixture', source_root=str(repo), base_commit=commit), workspace=dict(worktree_path=str(repo)))))
    save(cpath, m)
    return repo, cpath, m


def approved(e, cpath, m):
    m['review'] = dict(path='review.md', hash=ref('workflow', 'review.md', cpath.parent)['sha256'], reviewed_contract_hash=e.contract_hash(m), snapshot_id='sha256:' + '0'*64, verdict='APPROVED', ac=[dict(id='AC1', status='UNVERIFIED', reason='planned', checks=['command-check'])])
    m['review']['ac'].append(dict(m['review']['ac'][0], id='AC3'))
    save(cpath, m)


def test_registry_and_review_require_exact_active_set(contract):
    e = module()
    repo, cp, m = contract
    assert e.load_contract(cp)['review'] is None
    approved(e, cp, m)
    e.validate_review(cp, m)
    for change in (lambda x: x['active'].append(copy.deepcopy(x['active'][0])), lambda x: x['retired'].clear(), lambda x: x['review']['ac'].append(dict(id='AC2', status='SATISFIED', reason='x', checks=['command-check']))):
        broken = copy.deepcopy(m)
        change(broken)
        save(cp, broken)
        with pytest.raises(e.EvidenceError):
            loaded = e.load_contract(cp)
            e.validate_review(cp, loaded)
    save(cp, m)
    for key, value in [('version', True), ('checks', {}), ('allowlist', dict(version=1, paths=[], extra=1))]:
        broken = copy.deepcopy(m); broken[key] = value; save(cp, broken)
        with pytest.raises(e.EvidenceError): e.load_contract(cp)
    save(cp, m)
    path = cp.parent / 'evidence.json'
    path.write_text(path.read_text().replace('"version": 1', '"version": 1, "version": 1', 1))
    with pytest.raises(e.EvidenceError): e.load_contract(cp)
    save(cp, m)
    original = path.read_text()
    path.write_text(original.replace('"version": 1', '"version": NaN', 1))
    with pytest.raises(e.EvidenceError): e.load_contract(cp)
    save(cp, m)
    for field, value in [('expected_exit', True), ('kind', []), ('cwd', '../repo'), ('targets', ['fake']), ('assertions', [])]:
        broken = copy.deepcopy(m); broken['checks'][0][field] = value; save(cp, broken)
        with pytest.raises(e.EvidenceError): e.load_contract(cp)
    source = cp.parent / 'spec.md'
    original_source = source.read_text()
    source.write_text(original_source + '| AC1 | ACTIVE | duplicate |\n')
    broken = copy.deepcopy(m); broken['source'] = ref('workflow', 'spec.md', cp.parent); save(cp, broken)
    with pytest.raises(e.EvidenceError, match='E_AC_SET'): e.load_contract(cp)
    source.write_text(original_source)
    (repo / 'link').symlink_to(repo / 'input.txt')
    broken = copy.deepcopy(m); broken['checks'][0]['inputs'] = [ref('repo', 'link', repo)]; save(cp, broken)
    with pytest.raises(e.EvidenceError, match='E_EVIDENCE_PATH'): e.load_contract(cp)
    save(cp, m)
    m['checks'][0]['inputs'] = []
    save(cp, m)
    with pytest.raises(e.EvidenceError): e.load_contract(cp)


def test_command_uses_fixed_exit_and_output_assertions(contract):
    e = module(); repo, cp, m = contract
    receipt = e.run_check(cp, 'command-check')
    assert receipt['results'][0]['status'] == 'passed'
    assert receipt['cwd'] == 'sub'
    assert receipt['commit'] == subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    m['checks'][0]['expected_exit'] = 3; save(cp, m)
    assert e.run_check(cp, 'command-check')['results'][0]['status'] == 'failed'
    m['checks'][0]['expected_exit'] = 0
    m['checks'][0]['assertions'][0]['value'] = 'fixed'; save(cp, m)
    assert e.run_check(cp, 'command-check')['results'][0]['status'] == 'failed'
    cli = subprocess.run([sys.executable, str(ARTIFACT), 'evidence-run', '--context', str(cp), '--check', 'command-check'], capture_output=True, text=True)
    assert cli.returncode == 1
    assert json.loads(cli.stdout)['results'][0]['status'] == 'failed'
    m['checks'][0]['argv'] = [sys.executable, '-m', 'pytest']; save(cp, m)
    with pytest.raises(e.EvidenceError): e.run_check(cp, 'command-check')


def test_pytest_requires_current_exact_targets(contract):
    e = module(); repo, cp, m = contract
    test = repo / 'sub' / 'test_sample.py'
    test.write_text("import pytest\n@pytest.mark.parametrize('value', ['a.b', 'c'])\ndef test_ok(value): pass\n@pytest.mark.skip(reason='skip')\ndef test_skip(): pass\n")
    c = m['checks'][0]
    c.update(kind='pytest', argv=[sys.executable, '-m', 'pytest', 'test_sample.py::test_ok', '-q'], inputs=[ref('repo', 'sub/test_sample.py', repo)], targets=['sub/test_sample.py::test_ok[a.b]', 'sub/test_sample.py::test_ok[c]'], assertions=[])
    save(cp, m)
    cli = subprocess.run([sys.executable, str(ARTIFACT), 'evidence-run', '--context', str(cp), '--check', c['id']], capture_output=True, text=True)
    assert cli.returncode == 0, cli.stderr
    receipt = json.loads(cli.stdout)
    assert receipt['results'][0]['status'] == 'passed', receipt
    run = cp.parent / 'evidence/runs' / receipt['run_id']
    old_report = (run / 'junit.xml').read_bytes()
    c['targets'].append('sub/test_sample.py::missing'); save(cp, m)
    assert e.run_check(cp, c['id'])['results'][0]['status'] == 'failed'
    c['argv'] = [sys.executable, '-m', 'pytest', 'test_sample.py::test_skip', '-q']
    c['targets'] = ['sub/test_sample.py::test_skip']; save(cp, m)
    assert e.run_check(cp, c['id'])['results'][0]['status'] == 'failed'
    # A wrapper returning rc 0 without invoking pytest must not reuse an old report.
    c['argv'] = [sys.executable, '-c', 'pass']; save(cp, m)
    assert e.run_check(cp, c['id'])['results'][0]['status'] == 'failed'
    with pytest.raises(e.EvidenceError):
        e.parse_pytest(old_report, c['targets'], 'different-run')
    c['argv'] = [sys.executable, '-m', 'pytest', '--junitxml=stale.xml']; save(cp, m)
    with pytest.raises(e.EvidenceError): e.run_check(cp, c['id'])


def test_go_requires_executed_package_and_test_targets(contract):
    e = module(); repo, cp, m = contract
    events = [dict(Action='run', Package='example/p', Test='TestA'), dict(Action='run', Package='example/p', Test='TestA/sub'), dict(Action='pass', Package='example/p', Test='TestA/sub'), dict(Action='pass', Package='example/p', Test='TestA'), dict(Action='pass', Package='example/p')]
    c = m['checks'][0]
    c.update(kind='go_test', argv=[sys.executable, 'runner.py'], targets=[dict(package='example/p', test='TestA'), dict(package='example/p', test='TestA/sub')], assertions=[])
    for mutation, expected in [(lambda x: x, 'passed'), (lambda x: [v for v in x if v['Action'] != 'run'], 'failed'), (lambda x: x[:-1], 'failed'), (lambda x: x + [dict(Action='skip', Package='example/p', Test='TestA')], 'failed'), (lambda x: x + [dict(Action='output', Package='example/p', Output='ok example/p (cached)\n')], 'failed'), (lambda x: [], 'failed')]:
        payload = '\n'.join(json.dumps(x) for x in mutation(copy.deepcopy(events)))
        (repo / 'sub/runner.py').write_text('print(' + repr(payload) + ')\n')
        save(cp, m)
        assert e.run_check(cp, c['id'])['results'][0]['status'] == expected
    (repo / 'sub/runner.py').write_text("print('not json')\n")
    assert e.run_check(cp, c['id'])['results'][0]['status'] == 'failed'
    c['argv'] = ['go', 'test', '-json']; save(cp, m)
    with pytest.raises(e.EvidenceError): e.run_check(cp, c['id'])


def test_receipt_revalidates_contract_snapshot_inputs_and_raw_files(contract):
    e = module(); repo, cp, m = contract
    receipt = e.run_check(cp, 'command-check')
    assert e.validate_latest_receipt(cp, m, 'command-check')['run_id'] == receipt['run_id']
    raw = cp.parent / 'evidence/runs' / receipt['run_id'] / 'stdout.log'
    original = raw.read_bytes(); raw.write_bytes(b'tampered')
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    raw.write_bytes(original)
    (repo / 'input.txt').write_text('changed')
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    (repo / 'input.txt').write_text('input')
    (repo / 'sub/runner.py').write_text("print('changed')\n")
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    (repo / 'sub/runner.py').write_text("print('fixed')\n")
    changed = copy.deepcopy(m); changed['checks'][0]['assertions'][0]['value'] = 'different'; save(cp, changed)
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, changed, 'command-check')
    save(cp, m)
    run_dir = raw.parent
    inputs_path = run_dir / 'inputs.json'
    inputs_bytes = inputs_path.read_bytes(); inputs_path.write_bytes(b'{}')
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    inputs_path.write_bytes(inputs_bytes)
    receipt_path = run_dir / 'receipt.json'
    receipt_bytes = receipt_path.read_bytes()
    broken = json.loads(receipt_bytes); broken['exit_code'] = False; receipt_path.write_text(json.dumps(broken))
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    receipt_path.write_bytes(receipt_bytes)
    broken = json.loads(receipt_bytes); broken['sequence'] = True; receipt_path.write_text(json.dumps(broken))
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    receipt_path.write_bytes(receipt_bytes)
    approved(e, cp, m)
    assert e.validate_latest_receipt(cp, m, 'command-check')['run_id'] == receipt['run_id']


def test_latest_started_attempt_blocks_fallback_and_allows_successful_retry(contract, monkeypatch):
    e = module(); repo, cp, m = contract
    first = e.run_check(cp, 'command-check')
    # Environment changes exercise the SAME contract, snapshot and input set.
    (repo / 'sub/runner.py').write_text("import os\nprint(os.environ.get('EVIDENCE_TEST_OUTPUT', 'fixed'))\n")
    first = e.run_check(cp, 'command-check')
    monkeypatch.setenv('EVIDENCE_TEST_OUTPUT', 'bad')
    failed = e.run_check(cp, 'command-check')
    assert failed['results'][0]['status'] == 'failed'
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    monkeypatch.delenv('EVIDENCE_TEST_OUTPUT')
    good = e.run_check(cp, 'command-check')
    assert e.validate_latest_receipt(cp, m, 'command-check')['run_id'] == good['run_id']
    real_run = e.subprocess.run
    def interrupt(argv, **kwargs):
        if argv[0] == sys.executable: raise KeyboardInterrupt()
        return real_run(argv, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(e.subprocess, 'run', interrupt)
        with pytest.raises(KeyboardInterrupt): e.run_check(cp, 'command-check')
    with pytest.raises(e.EvidenceError): e.validate_latest_receipt(cp, m, 'command-check')
    retry = e.run_check(cp, 'command-check')
    assert retry['sequence'] == good['sequence'] + 2
    assert e.validate_latest_receipt(cp, m, 'command-check')['run_id'] == retry['run_id']


def test_collector_shares_workflow_directory_lock(contract):
    e = module(); _, cp, _ = contract
    fd = os.open(cp.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(e.EvidenceError, match='E_EVIDENCE_BUSY'): e.run_check(cp, 'command-check')
        assert not (cp.parent / 'evidence/runs').exists()
    finally:
        os.close(fd)
