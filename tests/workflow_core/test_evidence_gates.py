from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys

import pytest

from tests.workflow_core.test_workflow_evidence import contract, module, approved, save, ref
from tests.workflow_core.test_workflow_state import context_fixture


def state_module():
    path = module().__file__.replace('workflow_evidence.py', 'workflow_state.py')
    spec = importlib.util.spec_from_file_location('gate_state', path)
    state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state)
    return state


@pytest.fixture
def gate(contract):
    repo, cp, manifest = contract
    evidence = module()
    partial = json.loads(cp.read_text())
    context = context_fixture()
    context['identity'].update(partial['identity'], artifact_root=str(cp.parent))
    context['workspace'].update(partial['workspace'])
    context['state'].update(phase='FINAL_REVIEW', artifact_revision=0)
    context['shipping'] = dict.fromkeys(context['shipping'])
    cp.write_text(json.dumps(context))
    (cp.parent / 'reviews').mkdir()
    (cp.parent / 'reviews' / 'final-review.md').write_text('AC1 UNVERIFIED planned')
    (cp.parent / 'verification.md').write_text('## 失敗履歴\nなし\n## 未検証範囲\nなし\n')
    approved(evidence, cp, manifest)
    manifest['review']['snapshot_id'] = evidence._snapshot(repo, context, manifest)['snapshot_id']
    save(cp, manifest)
    return evidence, state_module(), repo, cp, manifest, context


def advance(state, cp, target, patch=None):
    current = state.load_context(cp)
    return state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=lambda c: state.transition_context(c, target, patch))


def grant_consent(e, state, cp):
    """Meet the new human gate through real CAS operations in legacy scenarios."""
    selected = dict(self_reason='既存規約で判断可能', blockers=[], cards=[], verification_assumptions=[])
    def command(operation):
        return e.human_review_command(cp, operation=operation,
            expected_revision=state.load_context(cp)['state']['artifact_revision'])
    assert command(dict(action='present', assessment=selected))['status'] == 'pending'
    record = state.load_context(cp)['execution']['human_review']
    assert command(dict(action='respond', presentation_id=record['presentations'][-1]['id'], targets=['self'], decision='approve_current',
                        user_citation=dict(role='user', reference='fixture:consent', quote='セルフレビューで通してください')))['status'] == 'passed'
    current = state.load_context(cp)
    if current['state']['phase'] == 'USER_DECISION_REQUIRED':
        state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=state.resume_context)


def rejected(state, cp, target, pattern, patch=None):
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match=pattern):
        advance(state, cp, target, patch)
    assert cp.read_bytes() == before


def test_review_rejects_unsatisfied_and_allows_planned_unverified(gate):
    e, state, repo, cp, m, context = gate
    m['review']['ac'][0]['status'] = 'UNSATISFIED'
    save(cp, m)
    rejected(state, cp, 'LOCAL_VERIFICATION', 'E_REVIEW')
    m['review']['ac'][0]['status'] = 'UNVERIFIED'
    save(cp, m)
    updated = advance(state, cp, 'LOCAL_VERIFICATION')
    assert updated['execution']['gates']['final_review']['status'] == 'passed'
    rejected(state, cp, 'LOCAL_COMPLETE', 'E_ATTEMPT')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    updated = advance(state, cp, 'LOCAL_COMPLETE')
    assert updated['execution']['gates']['local_verification']['status'] == 'passed'


def with_ci(e, cp, m):
    check = dict(id='remote', kind='gitlab_ci', argv=[], cwd=None,
                 inputs=copy.deepcopy(m['checks'][0]['inputs']), targets=['required'],
                 expected_exit=None, assertions=[])
    m['checks'].append(check)
    for ac in m['active']:
        ac['checks'] = [*ac['checks'], 'remote']
    m['ci'] = dict(host='git.example.invalid', project_id=1, required_jobs=['required'],
                   delegated_ac=['AC1', 'AC3'],
                   authorization_ref=dict(ref('workflow', 'plan.md', cp.parent), locator='approved delegation'))
    for ac in m['review']['ac']:
        ac['checks'] = [*ac['checks'], 'remote']
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)


def test_ci_delegation_requires_authorization_local_success_and_index_equality(gate):
    e, state, repo, cp, m, context = gate
    with_ci(e, cp, m)
    advance(state, cp, 'LOCAL_VERIFICATION')
    rejected(state, cp, 'COMMIT', 'E_ATTEMPT')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    rejected(state, cp, 'LOCAL_COMPLETE', 'E_ATTEMPT')
    rejected(state, cp, 'COMMIT', 'E_AUTHORIZATION')
    # Index differs while worktree/review/receipts still refer to the same tree.
    (repo / 'input.txt').write_text('index only')
    subprocess.run(['git', '-C', str(repo), 'add', 'input.txt'], check=True)
    (repo / 'input.txt').write_text('input')
    auth = {'authorization': {'shipping_authorized': True}}
    rejected(state, cp, 'COMMIT', 'E_SNAPSHOT', auth)
    subprocess.run(['git', '-C', str(repo), 'add', 'input.txt'], check=True)
    (repo / 'outside.txt').write_text('external')
    rejected(state, cp, 'COMMIT', 'E_SNAPSHOT', auth)
    (repo / 'outside.txt').unlink()
    updated = advance(state, cp, 'COMMIT', auth)
    assert updated['execution']['gates']['local_verification']['ci_pending'] is True
    # Cumulative LOCAL_COMPLETE cannot be weakened by COMMIT's CI exemption.
    context = state.load_context(cp)
    context['state']['phase'] = 'LOCAL_COMPLETE'
    cp.write_text(json.dumps(context))
    rejected(state, cp, 'COMMIT', 'E_ATTEMPT')


def test_legacy_forward_gate_is_atomic_and_can_resume_after_evidence_completion(gate):
    e, state, repo, cp, m, context = gate
    evidence_bytes = (cp.parent / 'evidence.json').read_bytes()
    (cp.parent / 'evidence.json').unlink()
    before = cp.read_bytes()
    assert state.main(['validate', '--context', str(cp)]) == 0
    rejected(state, cp, 'LOCAL_VERIFICATION', 'E_EVIDENCE')
    assert cp.read_bytes() == before
    stopped = state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=lambda c: state.stop_context(c, 'legacy'))
    before = cp.read_bytes()
    # FINAL_REVIEW means review is beginning; resume does not require completion.
    state.mutate_context(cp, expected_revision=stopped['state']['artifact_revision'], operation=state.resume_context)
    (cp.parent / 'evidence.json').write_bytes(evidence_bytes)
    advance(state, cp, 'LOCAL_VERIFICATION')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    advance(state, cp, 'LOCAL_COMPLETE')
    assert state.load_context(cp)['identity']['schema_version'] == 1


def test_forward_and_resume_recheck_cumulative_prerequisites(gate):
    e, state, repo, cp, m, context = gate
    advance(state, cp, 'LOCAL_VERIFICATION')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    advance(state, cp, 'LOCAL_COMPLETE')
    # Direct durable patches use the same gate as graph transitions.
    (cp.parent / 'review.md').write_text('changed')
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_EVIDENCE_HASH'):
        state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=lambda c: c['execution']['gates'].update(final_review='passed'))
    assert cp.read_bytes() == before
    rejected(state, cp, 'COMMIT', 'E_EVIDENCE_HASH', {'execution': {'gates': {'local_verification': 'passed'}}})
    stopped = state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=lambda c: state.stop_context(c, 'repair'))
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_EVIDENCE_HASH'):
        state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=state.resume_context)
    assert cp.read_bytes() == before
    (cp.parent / 'review.md').write_text('review.md')
    state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=state.resume_context)
    # A latest failed attempt is never replaced by an earlier successful run.
    (repo / 'sub' / 'runner.py').write_text("print('wrong')\n")
    # Keep the changed runner out of snapshot only for this separate evidence contract.
    m['allowlist']['paths'].remove('sub/runner.py')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    m['review']['snapshot_id'] = e._snapshot(repo, state.load_context(cp), m)['snapshot_id']
    save(cp, m)
    e.run_check(cp, 'command-check')
    rejected(state, cp, 'COMMIT', 'E_CHECK_RESULT')
    # Normative invalidation remains available with unusable evidence.
    state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=state.invalidate_normative_context)


def test_check_gates_is_read_only_and_cannot_use_passed_patch(gate):
    e, state, repo, cp, m, context = gate
    before = cp.read_bytes()
    assert state.main(['check-gates', '--context', str(cp), '--to', 'LOCAL_VERIFICATION']) == 0
    assert cp.read_bytes() == before
    advance(state, cp, 'LOCAL_VERIFICATION')
    before = cp.read_bytes()
    assert state.main(['check-gates', '--context', str(cp), '--to', 'LOCAL_COMPLETE']) == 1
    assert cp.read_bytes() == before
    rejected(state, cp, 'LOCAL_COMPLETE', 'E_ATTEMPT', {'execution': {'gates': {'local_verification': 'passed'}}})


def commit_fixture(repo):
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'verified'], check=True)
    return subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()


def test_committed_gates_do_not_recheck_live_index(gate):
    e, state, repo, cp, m, context = gate
    (repo / 'sub' / 'runner.py').write_text("print('fixed')\n# reviewed change\n")
    m['review']['snapshot_id'] = e._snapshot(repo, context, m)['snapshot_id']
    save(cp, m)
    advance(state, cp, 'LOCAL_VERIFICATION')
    receipt = e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    advance(state, cp, 'COMMIT', {'authorization': {'shipping_authorized': True}})
    commit = commit_fixture(repo)
    assert commit != receipt['commit']
    # External WIP/staged is irrelevant after committing the verified tree.
    (repo / 'outside.txt').write_text('unrelated source work')
    subprocess.run(['git', '-C', str(repo), 'add', 'outside.txt'], check=True)
    advanced = advance(state, cp, 'PUSH_MR', {'shipping': {'commit': commit}})
    assert advanced['execution']['review_snapshot_id'] == receipt['snapshot_before']['snapshot_id']
    advance(state, cp, 'CI')
    rejected(state, cp, 'MR_READY', 'E_CI')
    bad_commit = commit_fixture(repo)
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_SNAPSHOT'):
        state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=lambda c: c['shipping'].update(commit=bad_commit))
    assert cp.read_bytes() == before


@pytest.fixture
def retained(gate, tmp_path, monkeypatch):
    """Full cleanup integration: Task03 connects CI collector and export APIs."""
    e, state, source, cp, m, context = gate
    worktree = tmp_path / 'worktree'
    subprocess.run(['git', '-C', str(source), 'worktree', 'add', '-qb', 'reviewed', str(worktree)], check=True)
    context['workspace']['worktree_path'] = str(worktree)
    cp.write_text(json.dumps(context))
    m['active'][0]['oracle'] = dict(ref('repo', 'input.txt', worktree), locator='fixed input')
    with_ci(e, cp, m)
    (worktree / 'sub' / 'runner.py').write_text("import os\nprint('failed' if os.environ.get('FIXTURE_FAIL') else 'fixed')\n")
    m['review']['snapshot_id'] = e._snapshot(worktree, context, m)['snapshot_id']
    save(cp, m)
    advance(state, cp, 'LOCAL_VERIFICATION')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    subprocess.run(['git', '-C', str(worktree), 'add', '.'], check=True)
    advance(state, cp, 'COMMIT', {'authorization': {'shipping_authorized': True}})
    commit = commit_fixture(worktree)
    advance(state, cp, 'PUSH_MR', {'shipping': {'commit': commit}})
    advance(state, cp, 'CI')
    # Fake only the external transport, preserving collector parsing and receipts.
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    fake = bin_dir / 'glab'
    fake.write_text('#!' + sys.executable + '\nimport json,sys\n' +
                    'endpoint=sys.argv[-1]\n' +
                    'print(json.dumps(' + repr([dict(id=10, name='required', status='success',
                         pipeline=dict(id=1, project_id=1, sha=commit, status='success'), commit=dict(id=commit))]) +
                    ' if "/jobs?" in endpoint else ' +
                    repr(dict(id=1, project_id=1, sha=commit, status='success')) + '))\n')
    fake.chmod(0o755)
    import os
    monkeypatch.setenv('PATH', str(bin_dir) + os.pathsep + os.environ['PATH'])
    e.collect_ci(cp, 1)
    advance(state, cp, 'MR_READY')
    advance(state, cp, 'MERGE_CHECK')
    bundle = cp.parent / 'evidence' / 'cleanup'
    e.export_evidence(cp, bundle)
    return e, state, source, worktree, cp, m, bundle


def test_cleanup_uses_retained_evidence_after_worktree_removal(retained):
    e, state, source, worktree, cp, m, bundle = retained
    before = cp.read_bytes()
    assert state.main(['check-gates', '--context', str(cp), '--to', 'WT_REMOVE']) == 0
    assert cp.read_bytes() == before
    subprocess.run(['git', '-C', str(source), 'worktree', 'remove', str(worktree)], check=True)
    (source / 'input.txt').write_text('new source WIP')
    subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
    advance(state, cp, 'WT_REMOVE', {'workspace': {'worktree_path': None}})
    current = state.load_context(cp)
    stopped = state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=lambda c: state.stop_context(c, 'cleanup'))
    state.mutate_context(cp, expected_revision=stopped['state']['artifact_revision'], operation=state.resume_context)
    advance(state, cp, 'ARTIFACT_REMOVE')


@pytest.mark.parametrize('unfinished', [False, True])
def test_cleanup_rejects_retained_evidence_when_latest_attempt_changed(retained, unfinished, monkeypatch):
    e, state, source, worktree, cp, m, bundle = retained
    if unfinished:
        import uuid
        old_dir, start = e.latest_start(cp, m, 'command-check', m['review']['snapshot_id'])
        start = copy.deepcopy(start)
        start.update(run_id=str(uuid.uuid4()), sequence=max(s['sequence'] for _, s in e._starts(cp.parent)) + 1)
        directory = cp.parent / 'evidence' / 'runs' / start['run_id']
        directory.mkdir()
        e._atomic_new(directory / 'start.json', start)
    else:
        monkeypatch.setenv('FIXTURE_FAIL', '1')
        receipt = e.run_check(cp, 'command-check')
        assert receipt['results'][0]['status'] == 'failed'
    rejected(state, cp, 'WT_REMOVE', 'E_(ATTEMPT|EVIDENCE)')


@pytest.mark.parametrize('modified', [False, True])
def test_cleanup_rejects_missing_or_modified_retained_references_without_mutation(retained, modified):
    e, state, source, worktree, cp, m, bundle = retained
    path = bundle / 'repo' / 'input.txt'
    if modified:
        path.write_text('tampered')
    else:
        path.unlink()
    rejected(state, cp, 'WT_REMOVE', 'E_EVIDENCE')


def test_check_gates_and_transition_share_artifact_lint(gate, capsys):
    e, state, repo, cp, m, context = gate
    advance(state, cp, 'LOCAL_VERIFICATION')
    e.run_check(cp, 'command-check')
    grant_consent(e, state, cp)
    (cp.parent / 'verification.md').write_text('missing required headings')
    before = cp.read_bytes()
    assert state.main(['check-gates', '--context', str(cp), '--to', 'LOCAL_COMPLETE']) == 1
    assert 'verification.md: 失敗履歴の見出しと未検証範囲の見出しがどちらもない' in capsys.readouterr().err
    assert cp.read_bytes() == before
    assert state.main(['transition', '--context', str(cp), '--to', 'LOCAL_COMPLETE', '--expected-revision', str(state.load_context(cp)['state']['artifact_revision'])]) == 1
    assert 'verification.md: 失敗履歴の見出しと未検証範囲の見出しがどちらもない' in capsys.readouterr().err
    assert cp.read_bytes() == before
    (cp.parent / 'verification.md').write_text('## 失敗履歴\nなし\n## 未検証範囲\nなし\n')
    assert state.main(['check-gates', '--context', str(cp), '--to', 'LOCAL_COMPLETE']) == 0
    assert cp.read_bytes() == before
    assert state.main(['transition', '--context', str(cp), '--to', 'LOCAL_COMPLETE', '--expected-revision', str(state.load_context(cp)['state']['artifact_revision'])]) == 0
