from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys

import pytest

from tests.workflow_core.test_evidence_gates import gate, advance, rejected, with_ci, retained
from tests.workflow_core.test_evidence_ci_export import ci
from tests.workflow_core.test_workflow_evidence import contract, save, ref


def assessment(cp):
    return dict(self_reason='既存規約で判断可能', blockers=[], cards=[],
                verification_assumptions=[ref('workflow', 'plan.md', cp.parent)])


def command(e, state, cp, op):
    return e.human_review_command(cp, operation=op,
        expected_revision=state.load_context(cp)['state']['artifact_revision'])


def user_response(record, action='respond', targets=None, decision='approve_current'):
    op = dict(action=action, presentation_id=record['presentations'][-1]['id'], targets=targets or ['self'],
              user_citation=dict(role='user', reference='conversation:42', quote='セルフレビューで通してください'))
    if action == 'respond': op['decision'] = decision
    return op


def consent(e, state, cp, selected=None, resume=True):
    result = command(e, state, cp, dict(action='present', assessment=selected or assessment(cp)))
    assert result['status'] == 'pending'
    record = state.load_context(cp)['execution']['human_review']
    targets = [c['id'] for c in record['presentations'][-1]['assessment']['cards']] or ['self']
    result = command(e, state, cp, user_response(record, targets=targets))
    assert result['status'] == 'passed', result
    context = state.load_context(cp)
    if resume and context['state']['phase'] == 'USER_DECISION_REQUIRED':
        state.mutate_context(cp, expected_revision=context['state']['artifact_revision'], operation=state.resume_context)
    return state.load_context(cp)['execution']['human_review']


def test_local_completion_requires_presented_user_consent(gate):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION')
    e.run_check(cp, 'command-check')
    rejected(state, cp, 'LOCAL_COMPLETE', 'E_HUMAN_REVIEW_REQUIRED')
    assert state.main(['check-gates', '--context', str(cp), '--to', 'LOCAL_COMPLETE']) == 1
    script = cp.parent / 'op.json'
    script.write_text(json.dumps(dict(action='present', assessment=assessment(cp))))
    argv = [sys.executable, str(__import__('pathlib').Path(e.__file__).with_name('human_review.py')), '--context', str(cp), '--operation-file', str(script)]
    proc = subprocess.run(argv + ['--expected-revision', '1'], capture_output=True, text=True)
    assert proc.returncode == 1, proc.stderr
    assert json.loads(proc.stdout)['status'] == 'pending'
    context = state.load_context(cp)
    assert context['state']['phase'] == 'USER_DECISION_REQUIRED'
    script.write_text(json.dumps(user_response(context['execution']['human_review'])))
    proc = subprocess.run(argv + ['--expected-revision', str(context['state']['artifact_revision'])], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    context = state.load_context(cp)
    state.mutate_context(cp, expected_revision=context['state']['artifact_revision'], operation=state.resume_context)
    advance(state, cp, 'LOCAL_COMPLETE')


def test_consent_does_not_replace_required_review_or_local_receipts(gate):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION')
    before = cp.read_bytes()
    with pytest.raises((e.EvidenceError, state.StateError)):
        command(e, state, cp, dict(action='present', assessment=assessment(cp)))
    assert cp.read_bytes() == before
    e.run_check(cp, 'command-check')
    consent(e, state, cp)
    (cp.parent / 'review.md').write_text('changed review')
    rejected(state, cp, 'LOCAL_COMPLETE', 'E_EVIDENCE_HASH')


def test_changed_basis_invalidates_consent_but_valid_resume_preserves_it(gate):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION'); e.run_check(cp, 'command-check')
    record = consent(e, state, cp)
    advance(state, cp, 'LOCAL_COMPLETE')
    current = state.load_context(cp)
    state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=lambda c: state.stop_context(c, 'pause'))
    current = state.load_context(cp)
    resumed = state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=state.resume_context)
    assert resumed['execution']['human_review'] == record
    # A replacement local receipt changes the human basis even at the same snapshot.
    e.run_check(cp, 'command-check')
    rejected(state, cp, 'COMMIT', 'E_HUMAN_REVIEW_STALE', {'authorization': {'shipping_authorized': True}})


def test_missing_partial_or_unrelated_consent_blocks_transition_and_resume(gate):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION'); e.run_check(cp, 'command-check')
    selected = assessment(cp)
    evidence = ref('workflow', 'plan.md', cp.parent)
    def card(identifier):
        return dict(id=identifier, question='保守時の展開範囲', code=[dict(path='sub/runner.py', symbol='runner', excerpt="print('fixed')", reference=evidence)],
                    scenario='障害調査時', impact='調査手順の差', evidence=[evidence], unresolved_reason='チーム運用知識が必要',
                    options=[dict(id='a', description='展開'), dict(id='b', description='関数化')], recommendation='a', current_option='a', answer_scope='局所構成のみ',
                    conditions=[dict(satisfied=True, reason='条件を満たす', evidence=[evidence]) for _ in range(5)])
    selected['cards'] = [card('one'), card('two')]
    command(e, state, cp, dict(action='present', assessment=selected))
    record = state.load_context(cp)['execution']['human_review']
    assert command(e, state, cp, user_response(record, targets=['one']))['status'] == 'pending'
    before = cp.read_bytes()
    with pytest.raises((e.EvidenceError, state.StateError)):
        command(e, state, cp, user_response(record, targets=['self']))
    assert cp.read_bytes() == before
    # A direct patch claiming the final phase still runs the same gate.
    with pytest.raises(state.StateError, match='E_HUMAN_REVIEW_REQUIRED'):
        state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'],
            operation=lambda c: c['state'].update(phase='LOCAL_COMPLETE', stopped_from=None))
    assert cp.read_bytes() == before
    assert command(e, state, cp, user_response(record, targets=['two']))['status'] == 'passed'


def test_review_consent_never_grants_shipping_authorization(gate):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION'); e.run_check(cp, 'command-check')
    consent(e, state, cp)
    assert state.load_context(cp)['authorization']['shipping_authorized'] is False
    rejected(state, cp, 'COMMIT', 'E_AUTHORIZATION')


def test_ci_pending_consent_allows_authorized_commit_then_ci_success(ci):
    e, state, repo, cp, m, data, response, trace = ci
    record = consent(e, state, cp)
    assert record['presentations'][-1]['ci_pending'] is True
    before = record['presentations'][-1]['basis_hash']
    rejected(state, cp, 'MR_READY', 'E_ATTEMPT')
    e.collect_ci(cp, 1)
    advance(state, cp, 'MR_READY')
    assert state.load_context(cp)['execution']['human_review']['presentations'][-1]['basis_hash'] == before


def test_ci_failure_then_success_does_not_restore_old_consent(ci):
    e, state, repo, cp, m, data, response, trace = ci
    consent(e, state, cp)
    response['jobs'][0]['status'] = 'failed'; data.write_text(json.dumps(response)); e.collect_ci(cp, 1)
    rejected(state, cp, 'MR_READY', 'E_CI')
    response['jobs'][0]['status'] = 'success'; data.write_text(json.dumps(response)); e.collect_ci(cp, 1)
    rejected(state, cp, 'MR_READY', 'E_HUMAN_REVIEW_STALE')
    consent(e, state, cp)
    advance(state, cp, 'MR_READY')


def failed_abandoned_success(ci, monkeypatch):
    e, state, repo, cp, m, data, response, trace = ci
    consent(e, state, cp)
    response['jobs'][0]['status'] = 'failed'; data.write_text(json.dumps(response)); failed = e.collect_ci(cp, 1)[0]
    original = e.subprocess.run
    def interrupt(argv, **kwargs):
        if argv[0] == 'glab': raise KeyboardInterrupt()
        return original(argv, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(e.subprocess, 'run', interrupt)
        with pytest.raises(KeyboardInterrupt): e.collect_ci(cp, 1)
    _, abandoned = e.latest_start(cp, m, 'remote', m['review']['snapshot_id'])
    response['jobs'][0]['status'] = 'success'; data.write_text(json.dumps(response)); success = e.collect_ci(cp, 1)[0]
    rejected(state, cp, 'MR_READY', 'E_HUMAN_REVIEW_STALE')
    consent(e, state, cp)
    return failed, abandoned, success


def test_export_preserves_failed_and_abandoned_ci_history_after_reapproval(ci, tmp_path, monkeypatch):
    e, state, repo, cp, m, *_ = ci
    failed, abandoned, success = failed_abandoned_success(ci, monkeypatch)
    bundle = tmp_path / 'bundle'
    e.export_evidence(cp, bundle)
    record = json.loads((bundle / 'workflow/human-review.json').read_text())
    history = record['presentations'][-1]['basis']['ci_history']
    assert len(history) == 2
    assert failed['run_id'] in history[0]['receipt']['path']
    assert abandoned['run_id'] in history[1]['start']['path']
    assert success['run_id'] in history[1]['successor_start']['path']
    assert (bundle / 'workflow/evidence/runs' / failed['run_id'] / 'jobs.json').is_file()
    assert e.validate_export(bundle)['human_review'] == record


def test_retained_ci_history_validates_without_original_roots(ci, tmp_path, monkeypatch):
    e, state, repo, cp, m, *_ = ci
    failed_abandoned_success(ci, monkeypatch)
    bundle = tmp_path / 'bundle'; e.export_evidence(cp, bundle)
    shutil.rmtree(cp.parent); shutil.rmtree(repo)
    assert e.validate_export(bundle)['human_review']['presentations'][-1]['basis']['ci_history']


@pytest.mark.parametrize('field,mutation', [('start', 'delete'), ('receipt', 'delete'), ('jobs', 'tamper'), ('successor_start', 'delete'), ('successor_start', 'check'), ('successor_start', 'snapshot'), ('successor_start', 'sequence')])
def test_retained_ci_history_rejects_missing_tampered_or_invalid_successor_evidence(ci, tmp_path, monkeypatch, field, mutation):
    e, state, repo, cp, m, *_ = ci
    failed, abandoned, success = failed_abandoned_success(ci, monkeypatch)
    bundle = tmp_path / 'bundle'; e.export_evidence(cp, bundle)
    paths = dict(start=bundle / 'workflow/evidence/runs' / failed['run_id'] / 'start.json',
                 receipt=bundle / 'workflow/evidence/runs' / failed['run_id'] / 'receipt.json',
                 jobs=bundle / 'workflow/evidence/runs' / failed['run_id'] / 'jobs.json',
                 successor_start=bundle / 'workflow/evidence/runs' / success['run_id'] / 'start.json')
    path = paths[field]
    if mutation == 'delete': path.unlink()
    elif mutation == 'tamper': path.write_text('[]')
    else:
        start = json.loads(path.read_text())
        if mutation == 'check': start['check_ids'] = ['wrong']
        elif mutation == 'snapshot': start['snapshot_before']['snapshot_id'] = 'sha256:' + '0' * 64
        else: start['sequence'] = 0
        path.write_text(json.dumps(start))
    with pytest.raises(e.EvidenceError): e.validate_export(bundle)


def test_revocation_blocks_live_and_retained_completion(retained):
    e, state, source, worktree, cp, m, bundle = retained
    context = state.load_context(cp); record = context['execution']['human_review']
    result = command(e, state, cp, user_response(record, action='revoke'))
    assert result['status'] == 'blocked'
    stopped = state.load_context(cp)
    assert stopped['state']['phase'] == 'USER_DECISION_REQUIRED'
    assert stopped['state']['stopped_from'] == 'MERGE_CHECK'
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_HUMAN_REVIEW'):
        state.mutate_context(cp, expected_revision=stopped['state']['artifact_revision'], operation=state.resume_context)
    assert cp.read_bytes() == before
    with pytest.raises(e.EvidenceError, match='E_HUMAN_REVIEW'):
        e.resolve_cleanup_evidence(cp, stopped)


def test_artifact_removal_rechecks_consent_and_deletes_only_owned_artifact(retained):
    e, state, source, worktree, cp, m, bundle = retained
    # Relocate the real receipt fixture to the artifact manager's canonical path.
    destination = source / '.aidocs' / 'workflows' / 'fixture'
    destination.parent.mkdir(parents=True)
    shutil.move(str(cp.parent), destination)
    cp = destination / 'context.json'
    context = state.load_context(cp)
    context['identity']['artifact_root'] = str(destination)
    cp.write_text(json.dumps(context))
    keep = destination.parent / 'keep'; keep.mkdir(); (keep / 'note').write_text('preserve')
    advance(state, cp, 'WT_REMOVE')
    advance(state, cp, 'ARTIFACT_REMOVE')
    current = state.load_context(cp)
    argv = [sys.executable, str(__import__('pathlib').Path(e.__file__).with_name('workflow_artifact.py')), 'remove',
            '--project-root', str(source), '--workflow-id', 'fixture', '--authorize', 'ARTIFACT_REMOVE',
            '--expected-revision', str(current['state']['artifact_revision'])]
    before = cp.read_bytes()
    record_path = destination / 'evidence/cleanup/workflow/human-review.json'
    original = record_path.read_bytes(); record_path.write_text('{}')
    assert subprocess.run(argv, capture_output=True).returncode != 0
    assert cp.read_bytes() == before and destination.is_dir()
    record_path.write_bytes(original)
    proc = subprocess.run(argv, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert not destination.exists()
    assert (keep / 'note').read_text() == 'preserve'


def test_context_human_review_schema_and_duplicate_keys_are_rejected_atomically(gate):
    e, state, repo, cp, m, _ = gate
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_HUMAN_REVIEW_SCHEMA'):
        state.mutate_context(cp, expected_revision=0, operation=lambda c: c['execution'].update(human_review={}))
    assert cp.read_bytes() == before
    cp.write_text(before.decode().replace('"artifact_revision": 0', '"artifact_revision": 0, "artifact_revision": 1'))
    with pytest.raises(state.StateError, match='duplicate JSON key'):
        state.load_context(cp)


def test_revocation_after_worktree_removal_uses_retained_roots(retained):
    e, state, source, worktree, cp, m, bundle = retained
    subprocess.run(['git', '-C', str(source), 'worktree', 'remove', str(worktree)], check=True)
    advance(state, cp, 'WT_REMOVE', {'workspace': {'worktree_path': None}})
    record = state.load_context(cp)['execution']['human_review']
    result = command(e, state, cp, user_response(record, action='revoke'))
    assert result['status'] == 'blocked'
    assert state.load_context(cp)['state']['stopped_from'] == 'WT_REMOVE'
    assert e.human_review_command(cp)['status'] == 'blocked'
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_HUMAN_REVIEW'):
        state.mutate_context(cp, expected_revision=state.load_context(cp)['state']['artifact_revision'], operation=state.resume_context)
    assert cp.read_bytes() == before
    # A new presentation can reuse valid retained quality, but the old bundle
    # cannot conceal the live record's new revision at a cleanup gate.
    consent(e, state, cp, resume=False)
    with pytest.raises(e.EvidenceError, match='E_HUMAN_REVIEW_STALE'):
        e.resolve_cleanup_evidence(cp, state.load_context(cp))
    replacement = cp.parent / 'evidence/reapproved-cleanup'
    e.export_evidence(cp, replacement)
    assert e.validate_export(replacement)['human_review'] == state.load_context(cp)['execution']['human_review']
    shutil.rmtree(bundle)
    shutil.move(str(replacement), bundle)
    context = state.load_context(cp)
    state.mutate_context(cp, expected_revision=context['state']['artifact_revision'], operation=state.resume_context)
    advance(state, cp, 'ARTIFACT_REMOVE')


def human_cli(e, state, cp, op=None):
    from pathlib import Path
    argv = [sys.executable, str(Path(e.__file__).with_name('human_review.py')), '--context', str(cp)]
    if op is not None:
        operation_file = cp.parent / 'human-operation.json'
        operation_file.write_text(json.dumps(op))
        argv += ['--operation-file', str(operation_file), '--expected-revision', str(state.load_context(cp)['state']['artifact_revision'])]
    return subprocess.run(argv, capture_output=True, text=True)


@pytest.mark.parametrize('decision', ['revoke', 'request_change'])
@pytest.mark.parametrize('invalidated', ['reference', 'code'])
def test_negative_response_persists_when_workflow_basis_is_stale(gate, decision, invalidated):
    e, state, repo, cp, m, _ = gate
    advance(state, cp, 'LOCAL_VERIFICATION'); e.run_check(cp, 'command-check')
    record = consent(e, state, cp)
    advance(state, cp, 'LOCAL_COMPLETE')
    context = state.load_context(cp)
    path = cp.parent / 'review.md' if invalidated == 'reference' else repo / 'sub/runner.py'
    original = path.read_bytes()
    if invalidated == 'reference': path.unlink()
    else: path.write_text("print('changed after approval')")
    op = user_response(record, action='revoke') if decision == 'revoke' else user_response(record, decision='request_change')
    result = human_cli(e, state, cp, op)
    assert result.returncode == 1, result.stderr
    saved = state.load_context(cp)
    assert saved['state']['artifact_revision'] == context['state']['artifact_revision'] + 1
    assert saved['state']['phase'] == 'USER_DECISION_REQUIRED'
    assert saved['state']['stopped_from'] == 'LOCAL_COMPLETE'
    assert saved['execution']['human_review']['responses'][-1]['action'] == decision
    path.write_bytes(original)
    assert json.loads(human_cli(e, state, cp).stdout)['status'] == 'blocked'
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='E_HUMAN_REVIEW'):
        state.mutate_context(cp, expected_revision=saved['state']['artifact_revision'], operation=state.resume_context)
    assert cp.read_bytes() == before


def legacy_retained(retained):
    e, state, source, worktree, cp, m, bundle = retained
    subprocess.run(['git', '-C', str(source), 'worktree', 'remove', str(worktree)], check=True)
    context = state.load_context(cp)
    context['execution'].pop('human_review')
    context['workspace']['worktree_path'] = None
    context['state'].update(phase='WT_REMOVE', stopped_from=None)
    cp.write_text(json.dumps(context))
    (bundle / 'workflow/human-review.json').unlink()
    return e, state, source, cp, m, bundle


def test_legacy_retained_quality_bootstraps_first_consent_after_worktree_removal(retained):
    e, state, source, cp, m, bundle = legacy_retained(retained)
    assert state.main(['check-gates', '--context', str(cp), '--to', 'ARTIFACT_REMOVE']) == 1
    result = human_cli(e, state, cp, dict(action='present', assessment=assessment(cp)))
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['status'] == 'pending'
    current = state.load_context(cp)
    assert current['state']['stopped_from'] == 'WT_REMOVE'
    record = current['execution']['human_review']
    assert human_cli(e, state, cp, user_response(record)).returncode == 0
    # Approval alone must not turn the legacy bundle into valid cleanup evidence.
    with pytest.raises(e.EvidenceError): e.resolve_cleanup_evidence(cp, state.load_context(cp))
    replacement = cp.parent / 'evidence/first-approved-cleanup'
    e.export_evidence(cp, replacement)
    assert e.validate_export(replacement)['human_review'] == state.load_context(cp)['execution']['human_review']
    shutil.rmtree(bundle); shutil.move(str(replacement), bundle)
    current = state.load_context(cp)
    state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=state.resume_context)
    advance(state, cp, 'ARTIFACT_REMOVE')


@pytest.mark.parametrize('missing', ['review', 'receipt', 'raw', 'fixed_commit'])
def test_legacy_retained_bootstrap_rejects_incomplete_or_wrong_commit_evidence(retained, missing):
    e, state, source, cp, m, bundle = legacy_retained(retained)
    if missing == 'fixed_commit':
        context = state.load_context(cp); context['shipping']['commit'] = context['identity']['base_commit']
        cp.write_text(json.dumps(context))
    elif missing == 'review': (bundle / 'workflow/review.md').unlink()
    else:
        directory, _ = e.latest_start(bundle / 'workflow/context.json', m, 'command-check', m['review']['snapshot_id'])
        (directory / ('receipt.json' if missing == 'receipt' else 'stdout.log')).unlink()
    before = cp.read_bytes()
    result = human_cli(e, state, cp, dict(action='present', assessment=assessment(cp)))
    assert result.returncode == 2, result.stdout
    assert cp.read_bytes() == before


def test_legacy_retained_bootstrap_preserves_failed_and_abandoned_ci_history(retained, monkeypatch):
    e, state, source, worktree, cp, m, bundle = retained
    transport = source.parent / 'bin/glab'
    original_transport = transport.read_text()
    transport.write_text(original_transport.replace("'status': 'success'", "'status': 'failed'"))
    failed = e.collect_ci(cp, 1)[0]
    assert failed['results'][0]['status'] == 'failed'
    original_run = e.subprocess.run
    def interrupt(argv, **kwargs):
        if argv[0] == 'glab': raise KeyboardInterrupt()
        return original_run(argv, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(e.subprocess, 'run', interrupt)
        with pytest.raises(KeyboardInterrupt): e.collect_ci(cp, 1)
    transport.write_text(original_transport)
    e.collect_ci(cp, 1)
    consent(e, state, cp)
    shutil.rmtree(bundle); e.export_evidence(cp, bundle)
    e, state, source, cp, m, bundle = legacy_retained(retained)
    history, _ = e._ci_history(cp.parent, m, m['review']['snapshot_id'])
    assert len(history) == 2
    result = human_cli(e, state, cp, dict(action='present', assessment=assessment(cp)))
    assert result.returncode == 1, result.stderr
    record = state.load_context(cp)['execution']['human_review']
    assert record['presentations'][-1]['basis']['ci_history'] == history
    assert human_cli(e, state, cp, user_response(record)).returncode == 0
    replacement = cp.parent / 'evidence/first-approved-with-history'
    e.export_evidence(cp, replacement)
    assert (replacement / 'workflow/evidence/runs' / failed['run_id'] / 'jobs.json').is_file()
    assert e.validate_export(replacement)['human_review']['presentations'][-1]['basis']['ci_history'] == history
