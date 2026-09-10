from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "dot_agents/workflows/software_delivery/scripts/workflow_merge.py"


def module():
    spec = importlib.util.spec_from_file_location("workflow_merge_test", SCRIPT)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def setup(monkeypatch, tmp_path):
    m = module()
    sha = "a" * 40
    context = {
        "shipping": {"commit": sha},
        "workspace": {"branch": "feature"},
        "identity": {"default_branch": "main"},
        "state": {"phase": "CI", "stopped_from": None},
    }
    manifest = {"ci": {"host": "git.example.invalid", "project_id": 7}}
    monkeypatch.setattr(m.state, "load_context", lambda _: context)
    monkeypatch.setattr(m.evidence, "load_contract", lambda *_: manifest)
    monkeypatch.setattr(m.evidence, "repository", lambda _: tmp_path)
    monkeypatch.setattr(m.evidence, "collect_ci", lambda *_: [])
    monkeypatch.setattr(m.evidence, "evaluate_gates", lambda *_: {"gates": {}})
    mr = {"iid": 3, "target_project_id": 7, "source_project_id": 7,
          "target_branch": "main", "source_branch": "feature", "sha": sha,
          "state": "opened", "draft": False,
          "head_pipeline": {"id": 11, "sha": sha, "status": "success"}}
    project = {"id": 7, "only_allow_merge_if_pipeline_succeeds": True,
               "allow_merge_on_skipped_pipeline": False}
    calls = []

    def fake_glab(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "projects/7":
            return subprocess.CompletedProcess(argv, 0, json.dumps(project), "")
        if argv[-1].endswith("/merge"):
            return subprocess.CompletedProcess(argv, 0, json.dumps(dict(mr, state="merged")), "")
        return subprocess.CompletedProcess(argv, 0, json.dumps(mr), "")

    monkeypatch.setattr(m.subprocess, "run", fake_glab)
    return m, tmp_path / "context.json", sha, calls


def test_check_only_never_puts(monkeypatch, tmp_path):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    result = m.merge(context, 3, sha)
    assert result["status"] == "checked"
    assert [argv[5] for argv in calls] == ["GET", "GET"]
    assert all(not argv[-1].endswith("/merge") for argv in calls)


def test_authorized_merge_uses_fixed_sha_once(monkeypatch, tmp_path):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    result = m.merge(context, 3, sha, authorize=True)
    assert result["status"] == "merged"
    assert [argv[5] for argv in calls] == ["GET", "GET", "GET", "PUT"]
    assert calls[-1][-1].endswith("/merge")
    assert "sha=" + sha in calls[-1]
    assert "should_remove_source_branch=true" in calls[-1]


@pytest.mark.parametrize("field,value", [
    ("sha", "b" * 40),
    ("target_project_id", 8),
    ("source_project_id", 8),
    ("target_branch", "release"),
    ("source_branch", "other"),
    ("draft", True),
])
def test_invalid_mr_is_rejected_without_put(monkeypatch, tmp_path, field, value):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    original = m._json_call

    def changed(argv, cwd):
        response = original(argv, cwd)
        if "/merge_requests/" in argv[-1] and not argv[-1].endswith("/merge"):
            response[field] = value
        return response

    monkeypatch.setattr(m, "_json_call", changed)
    with pytest.raises(m.MergeError):
        m.merge(context, 3, sha, authorize=True)
    assert all(not argv[-1].endswith("/merge") for argv in calls)


def test_source_head_race_is_reported_without_put(monkeypatch, tmp_path):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    original = m._json_call
    count = 0

    def raced(argv, cwd):
        nonlocal count
        response = original(argv, cwd)
        if "/merge_requests/" in argv[-1] and not argv[-1].endswith("/merge"):
            count += 1
            if count == 2:
                response["sha"] = "b" * 40
        return response

    monkeypatch.setattr(m, "_json_call", raced)
    with pytest.raises(m.MergeError) as error:
        m.merge(context, 3, sha, authorize=True)
    assert error.value.exit_code == 1
    assert "E_MERGE_RACE" in str(error.value)
    assert all(not argv[-1].endswith("/merge") for argv in calls)


from tests.workflow_core.test_workflow_evidence import contract
from tests.workflow_core.test_evidence_gates import gate
from tests.workflow_core.test_evidence_ci_export import ci


@pytest.fixture
def integration(ci, monkeypatch):
    e, state, repo, cp, manifest, data, response, trace = ci
    context = state.load_context(cp)
    sha = context['shipping']['commit']
    response['mr'] = dict(iid=3, project_id=1, source_project_id=1, target_project_id=1,
        source_branch=context['workspace']['branch'], target_branch=context['identity']['default_branch'],
        sha=sha, state='opened', draft=False, head_pipeline=dict(id=1, sha=sha, status='success'))
    response['project'] = dict(id=1, only_allow_merge_if_pipeline_succeeds=True,
        allow_merge_on_skipped_pipeline=False)
    data.write_text(json.dumps(response))
    fake = data.parent / 'bin' / 'glab'
    fake.write_text('#!' + sys.executable + '\n' + '''import json, os, sys
from pathlib import Path
import fcntl
trace = Path(os.environ['FAKE_TRACE'])
calls = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
with trace.open('a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
data = json.loads(Path(os.environ['FAKE_DATA']).read_text())
endpoint = sys.argv[-1]
if '/merge_requests/' in endpoint and any('/merge_requests/' in call[-1] for call in calls):
    fd = os.open(Path(os.environ['FAKE_CONTEXT']).parent, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        raise AssertionError('merge boundary must hold the workflow lock')
    finally:
        os.close(fd)
if '/jobs?' in endpoint and data.get('local_race'):
    cp = Path(os.environ['FAKE_CONTEXT'])
    context = json.loads(cp.read_text())
    context['execution']['human_review'] = None
    cp.write_text(json.dumps(context))
if endpoint == 'projects/1':
    result = data['project']
elif endpoint.endswith('/merge'):
    result = dict(data['mr'], state='merged')
    result.update(data.get('merge_override', {}))
elif '/merge_requests/' in endpoint:
    result = data['mr']
    if any('/merge_requests/' in call[-1] for call in calls):
        result.update(data.get('race', {}))
else:
    result = data['jobs' if '/jobs?' in endpoint else 'pipeline']
if data.get('api_failure') or (endpoint.endswith('/merge') and data.get('put_failure')):
    print('API failed', file=sys.stderr)
    sys.exit(1)
print(json.dumps(result))
''')
    monkeypatch.setenv('FAKE_CONTEXT', str(cp))
    return e, state, repo, cp, manifest, data, response, trace, sha


def run_cli(fixture, authorize=True):
    _, _, _, cp, _, data, response, trace, sha = fixture
    data.write_text(json.dumps(response))
    argv = [sys.executable, str(SCRIPT), '--context', str(cp), '--mr', '3', '--sha', sha]
    if authorize:
        argv += ['--authorize', 'MERGE']
    result = subprocess.run(argv, capture_output=True, text=True)
    calls = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
    return result, calls


@pytest.mark.parametrize('authorize', [False, True])
def test_real_cli_passes_real_gates(integration, authorize):
    result, calls = run_cli(integration, authorize)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == ('merged' if authorize else 'checked')
    puts = [call for call in calls if 'PUT' in call]
    assert len(puts) == int(authorize)
    assert any('/pipelines/1/jobs?' in call[-1] for call in calls)
    assert any(call[-1] == 'projects/1' and 'git.example.invalid' in call for call in calls)
    assert all(call[-1].startswith('projects/1/') or call[-1] == 'projects/1' for call in calls if 'git.example.invalid' in call)
    if authorize:
        assert 'sha=' + integration[-1] in puts[0]
        assert 'should_remove_source_branch=true' in puts[0]


@pytest.mark.parametrize('case', ['state', 'manifest', 'receipt', 'human', 'review', 'failed', 'skipped',
    'iid', 'sha', 'target_branch', 'source_branch', 'source_project_id', 'target_project_id',
    'draft', 'pipeline_bool', 'sha_race', 'pipeline_race', 'pipeline_status_race', 'pipeline_failed_race', 'pipeline_missing_race', 'policy_false', 'policy_missing', 'policy_string', 'policy_id', 'policy_api_failure', 'policy_skipped', 'policy_skipped_missing', 'api_failure', 'local_race', 'repo', 'shipping_sha'])
def test_real_cli_rejects_without_put(integration, case):
    e, state, repo, cp, manifest, data, response, trace, sha = integration
    if case == 'state': cp.unlink()
    elif case == 'manifest': (cp.parent / 'evidence.json').unlink()
    elif case == 'receipt': next((cp.parent / 'evidence' / 'runs').glob('*/receipt.json')).unlink()
    elif case == 'human':
        context = state.load_context(cp)
        context['execution']['human_review'] = None
        cp.write_text(json.dumps(context))
    elif case == 'review': (cp.parent / 'review.md').write_text('changed')
    elif case in ('failed', 'skipped'): response['jobs'][0]['status'] = case
    elif case in ('iid', 'source_project_id', 'target_project_id'): response['mr'][case] = 8
    elif case in ('sha', 'source_branch', 'target_branch'): response['mr'][case] = 'wrong'
    elif case == 'draft': response['mr']['draft'] = True
    elif case == 'pipeline_bool': response['mr']['head_pipeline']['id'] = True
    elif case == 'sha_race': response['race'] = dict(sha='b' * 40)
    elif case == 'pipeline_race': response['race'] = dict(head_pipeline=dict(id=2, sha=sha))
    elif case == 'pipeline_status_race': response['race'] = dict(head_pipeline=dict(id=1, sha=sha, status='running'))
    elif case == 'pipeline_failed_race': response['race'] = dict(head_pipeline=dict(id=1, sha=sha, status='failed'))
    elif case == 'pipeline_missing_race': response['race'] = dict(head_pipeline=dict(id=1, sha=sha))
    elif case == 'policy_false': response['project']['only_allow_merge_if_pipeline_succeeds'] = False
    elif case == 'policy_missing': response['project'].pop('only_allow_merge_if_pipeline_succeeds')
    elif case == 'policy_string': response['project']['only_allow_merge_if_pipeline_succeeds'] = 'true'
    elif case == 'policy_skipped': response['project']['allow_merge_on_skipped_pipeline'] = True
    elif case == 'policy_skipped_missing': response['project'].pop('allow_merge_on_skipped_pipeline')
    elif case == 'policy_id': response['project']['id'] = True
    elif case == 'policy_api_failure': response['api_failure'] = True
    elif case in ('api_failure', 'local_race'): response[case] = True
    elif case in ('repo', 'shipping_sha'):
        context = state.load_context(cp)
        if case == 'repo': context['workspace']['worktree_path'] = str(repo / 'missing')
        else: context['shipping']['commit'] = 'b' * 40
        cp.write_text(json.dumps(context))
    result, calls = run_cli(integration)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'Traceback' not in result.stderr
    assert not any('PUT' in call for call in calls)
    if case in ('sha_race', 'pipeline_race', 'pipeline_status_race', 'pipeline_failed_race', 'pipeline_missing_race'): assert 'E_MERGE_RACE' in result.stderr
    if case == 'local_race': assert 'E_HUMAN_REVIEW' in result.stderr


@pytest.mark.parametrize('field,value', [('iid', 4), ('source_project_id', 2), ('target_project_id', 2), ('sha', 'wrong'), ('state', 'opened')])
def test_real_cli_rejects_unknown_merge_result_without_retry(integration, field, value):
    integration[6]['merge_override'] = {field: value}
    result, calls = run_cli(integration)
    assert result.returncode == 1
    assert len([call for call in calls if 'PUT' in call]) == 1



def test_real_cli_put_failure_is_not_retried(integration):
    integration[6]['put_failure'] = True
    result, calls = run_cli(integration)
    assert result.returncode == 1
    assert len([call for call in calls if 'PUT' in call]) == 1


@pytest.mark.parametrize('iid', [True, False, 0, -1])
def test_invalid_iid_is_rejected_before_api(monkeypatch, tmp_path, iid):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    with pytest.raises(m.MergeError, match='positive integer'):
        m.merge(context, iid, sha, authorize=True)
    assert not calls


@pytest.mark.parametrize('length', [39, 41, 63, 65])
def test_partial_sha_is_rejected_before_api(monkeypatch, tmp_path, length):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    with pytest.raises(m.MergeError, match='full hexadecimal'):
        m.merge(context, 3, 'a' * length, authorize=True)
    assert not calls


def test_full_sha256_is_accepted(monkeypatch, tmp_path):
    m, context, sha, calls = setup(monkeypatch, tmp_path)
    sha = 'a' * 64
    m.state.load_context(context)['shipping']['commit'] = sha
    original = m._json_call
    def sha256(argv, cwd):
        response = original(argv, cwd)
        response['sha'] = sha
        if 'head_pipeline' in response:
            response['head_pipeline']['sha'] = sha
        return response
    monkeypatch.setattr(m, '_json_call', sha256)
    assert m.merge(context, 3, sha, authorize=True)['status'] == 'merged'
