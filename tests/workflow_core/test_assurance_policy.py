from __future__ import annotations
import copy
import hashlib
import json
import sys
import uuid

import pytest

from tests.workflow_core.test_evidence_gates import gate, advance, grant_consent
from tests.workflow_core.test_human_review import change, hr, cli, read, response
from tests.workflow_core.test_workflow_evidence import contract, module, save, ref


def assurance(risk='low'):
    return dict(risk=risk, reason='既存契約の局所変更', existing_contract=True,
                bounded_blast=True, adequate_oracle=True, protected_boundaries=[], risks=[], important=[])


def test_v2_manifest_and_shared_check(contract):
    repo, cp, m = contract
    m.update(version=2, assurance=assurance())
    save(cp, m)
    assert module().load_contract(cp)['assurance']['risk'] == 'low'


def test_policy_trigger_mapping(contract):
    repo, cp, m = contract
    e = module()
    a = assurance('medium')
    a['risks'] = [dict(kind='performance', checks=['command-check'])]
    e.validate_assurance(a, m['active'], m['checks'])
    a['risks'][0]['kind'] = 'security'
    with pytest.raises(e.EvidenceError): e.validate_assurance(a, m['active'], m['checks'])


def test_high_requires_boundary_and_nonconcrete_oracle(contract):
    _, _, m = contract
    e = module(); a = assurance('high')
    with pytest.raises(e.EvidenceError): e.validate_assurance(a, m['active'], m['checks'])
    a['protected_boundaries'] = ['API response']
    a['important'] = [dict(id='AC1', needs=[dict(kind='negative', checks=['command-check'])])]
    e.validate_assurance(a, m['active'], m['checks'])
    a['important'][0]['needs'][0]['checks'] = ['unknown']
    with pytest.raises(e.EvidenceError): e.validate_assurance(a, m['active'], m['checks'])

def freeze(gate):
    e, state, repo, cp, m, context = gate
    m.update(version=2, assurance=assurance())
    save(cp, m)
    context['state']['phase'] = 'WORKTREE_READY'
    cp.write_text(json.dumps(context))
    advance(state, cp, 'TASKS')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)
    return state.load_context(cp)


def test_freeze_shared_receipt_and_low_formal_without_response(gate):
    e, state, repo, cp, m, _ = gate
    freeze(gate)
    receipt = e.run_check(cp, 'command-check')
    advance(state, cp, 'FINAL_REVIEW')
    selected = dict(self_reason='既存挙動を保持', blockers=[], cards=[], verification_assumptions=[])
    result = e.human_review_command(cp, operation=dict(action='present', assessment=selected),
                                    expected_revision=state.load_context(cp)['state']['artifact_revision'])
    assert result['status'] == 'passed'
    current = state.load_context(cp)
    assert current['execution']['human_review']['responses'] == []
    assert current['state']['phase'] == 'FINAL_REVIEW'
    advance(state, cp, 'LOCAL_VERIFICATION')
    final = advance(state, cp, 'LOCAL_COMPLETE')
    assert len(final['execution']['gates']['local_verification']['run_ids']) == 1


@pytest.mark.parametrize('alter', ['assertions', 'source', 'need', 'downgrade', 'missing'])
def test_frozen_oracle_cannot_change(gate, alter):
    e, state, repo, cp, m, _ = gate
    current = freeze(gate)
    if alter == 'assertions':
        m['checks'][0]['assertions'][0]['value'] = 'weaker'
    elif alter == 'source':
        source = cp.parent / 'spec.md'
        source.write_text(source.read_text() + '\nweaker expectation\n')
        m['source'] = ref('workflow', 'spec.md', cp.parent)
        for ac in m['active']:
            ac['oracle']['sha256'] = m['source']['sha256']
    elif alter == 'need':
        m['assurance']['important'] = [dict(id='AC1', needs=[dict(kind='negative', checks=['command-check'])])]
    elif alter == 'downgrade':
        m['version'] = 1
        del m['assurance']
    else:
        current['execution']['gates'].pop('assurance_contract')
        cp.write_text(json.dumps(current))
    save(cp, m)
    with pytest.raises(e.EvidenceError, match='E_ASSURANCE_FIXED'):
        e.run_check(cp, 'command-check')


def test_input_hash_update_allowed_but_patch_overwrite_rejected(gate):
    e, state, repo, cp, m, _ = gate
    original = freeze(gate)['execution']['gates']['assurance_contract']
    (repo / 'input.txt').write_text('new input')
    m['checks'][0]['inputs'] = [ref('repo', 'input.txt', repo)]
    save(cp, m)
    e.run_check(cp, 'command-check')
    assert state.load_context(cp)['execution']['gates']['assurance_contract'] == original
    with pytest.raises(state.StateError, match='E_ASSURANCE_FIXED'):
        advance(state, cp, 'DEBUGGING', dict(execution=dict(gates=dict(assurance_contract=dict(projection_hash='forged')))))
    current = state.load_context(cp)
    changed = state.mutate_context(cp, expected_revision=current['state']['artifact_revision'], operation=state.invalidate_normative_context)
    assert changed['execution']['gates']['assurance_contract'] is None


def test_first_freeze_allows_uncreated_test_input(gate):
    e, state, repo, cp, m, context = gate
    m['checks'][0]['inputs'].append(dict(root='repo', path='new-test.py', sha256='0' * 64))
    freeze(gate)
    with pytest.raises(e.EvidenceError, match='E_EVIDENCE_PATH'):
        e.run_check(cp, 'command-check')


def direct_v2(change):
    op = change['op']; q = op['quality']
    oracle_text = b'base\n'
    q['assurance'] = assurance()
    q['oracle'] = dict(root='repo', path='x', sha256=hashlib.sha256(oracle_text).hexdigest(), locator='existing x contract')
    (change['repo'] / 'x').write_bytes(oracle_text)
    target = hr._snapshot_target(op['scope'], op['target'])
    for row in q['reviews']:
        row['snapshot_id'] = target['snapshot_id']
    definition = dict(id='check-1', kind='command',
                      argv=[sys.executable, '-c', "import os, sys; print('fixed'); sys.exit(1 if os.environ.get('DIRECT_TEST_FAIL') else 0)"], cwd='.',
                      inputs=[dict(root='repo', path='x', sha256=q['oracle']['sha256'])], targets=[], expected_exit=0,
                      assertions=[dict(stream='stdout', op='equals', value='fixed\n')])
    change['collect'] = dict(action='collect', scope=op['scope'], target=op['target'], oracle=q['oracle'], definition=definition)
    collected = hr.collect_direct(change['path'], change['collect'])
    q['validation']['checks'] = [dict(definition=definition, receipt=collected['receipt'])]
    return op


def direct_receipt(change):
    row = change['op']['quality']['validation']['checks'][0]
    return change['path'].parent / row['receipt']['path']


def test_direct_low_auto_raw_validation_and_revoke(change):
    op = direct_v2(change)
    result = cli(change, op, 0)
    assert result.returncode == 0, result.stderr
    record = read(change)
    assert record['responses'] == []
    assert '回答は不要' in record['presentations'][-1]['prompt']
    revoke = response(record, decision='request_change')
    assert cli(change, revoke, 1).returncode == 1
    assert cli(change).returncode == 1


@pytest.mark.parametrize('alter', ['missing', 'oracle', 'definition', 'raw_hash', 'receipt_hash'])
def test_direct_low_rejects_unreliable_validation(change, alter):
    op = direct_v2(change); q = op['quality']; row = q['validation']['checks'][0]
    if alter == 'missing': del row['definition']
    elif alter == 'oracle': q['oracle'] = dict(change['proof'], locator='new spec')
    elif alter == 'definition': row['definition']['argv'] = ['echo', 'wrong']
    elif alter == 'raw_hash': (direct_receipt(change).parent / 'stdout.log').write_text('changed')
    else: direct_receipt(change).write_text('{}')
    assert cli(change, op, 0).returncode != 0


def test_high_requires_all_boundary_approvals(gate):
    e, state, repo, cp, m, context = gate
    m.update(version=2, assurance=assurance('high'))
    m['assurance'].update(protected_boundaries=['API', 'storage'],
                          important=[dict(id='AC1', needs=[dict(kind='invariant', checks=['command-check'])])])
    save(cp, m)
    context['state']['phase'] = 'WORKTREE_READY'; cp.write_text(json.dumps(context))
    advance(state, cp, 'TASKS')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m); save(cp, m)
    e.run_check(cp, 'command-check')
    advance(state, cp, 'FINAL_REVIEW')
    proof = ref('workflow', 'review.md', cp.parent)
    assessment = dict(self_reason='境界確認', blockers=[], cards=[], verification_assumptions=[], boundary_cards=[])
    def command(operation):
        return e.human_review_command(cp, operation=operation, expected_revision=state.load_context(cp)['state']['artifact_revision'])
    with pytest.raises(e.EvidenceError): command(dict(action='present', assessment=assessment))
    for name in ('API', 'storage'):
        assessment['boundary_cards'].append(dict(id=name, boundary=name, question='この境界を承認しますか',
            code=[dict(path='input.txt', symbol='input', excerpt='input', reference=proof)],
            scenario='既存利用', impact='境界挙動', evidence=[proof], answer_scope='現在の境界'))
    assert command(dict(action='present', assessment=assessment))['status'] == 'pending'
    record = state.load_context(cp)['execution']['human_review']
    answer = response(record, targets=['API'])
    assert command(answer)['status'] == 'pending'
    answer['targets'] = ['storage']
    assert command(answer)['status'] == 'passed'


@pytest.mark.parametrize('alter', ['low_trigger', 'unknown', 'empty', 'duplicate', 'not_bounded', 'concrete_only'])
def test_invalid_risk_declarations(contract, alter):
    _, _, m = contract
    e = module(); a = assurance()
    if alter == 'low_trigger': a['risks'] = [dict(kind='integration', checks=['command-check'])]
    elif alter == 'unknown':
        a['risk'] = 'medium'; a['risks'] = [dict(kind='imaginary', checks=['command-check'])]
    elif alter == 'empty':
        a['risk'] = 'medium'; a['risks'] = [dict(kind='performance', checks=[])]
    elif alter == 'duplicate':
        a['risk'] = 'medium'; a['risks'] = [dict(kind='performance', checks=['command-check'])] * 2
    elif alter == 'not_bounded': a['risk'] = 'medium'; a['bounded_blast'] = False
    else:
        a.update(risk='high', protected_boundaries=['API'], important=[dict(id='AC1', needs=[dict(kind='concrete', checks=['command-check'])])])
    with pytest.raises(e.EvidenceError): e.validate_assurance(a, m['active'], m['checks'])


def test_medium_summary_requires_current_consent_and_inadequate_oracle_blocks(gate):
    e, state, repo, cp, m, context = gate
    m.update(version=2, assurance=assurance('medium'))
    save(cp, m)
    context['state']['phase'] = 'WORKTREE_READY'; cp.write_text(json.dumps(context))
    advance(state, cp, 'TASKS')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m); save(cp, m)
    e.run_check(cp, 'command-check'); advance(state, cp, 'FINAL_REVIEW')
    assessment = dict(self_reason='既存の入力を処理する。残る仮定は検証証跡を参照', blockers=[], cards=[], verification_assumptions=[])
    def command(op):
        return e.human_review_command(cp, operation=op, expected_revision=state.load_context(cp)['state']['artifact_revision'])
    assert command(dict(action='present', assessment=assessment))['status'] == 'pending'
    record = state.load_context(cp)['execution']['human_review']
    assert record['version'] == 2
    prompt = record['presentations'][-1]['prompt']
    assert 'MEDIUM: 変更挙動・重要な証跡・残余リスクを確認' in prompt
    assert '現在の案を承認します' in prompt
    assert 'セルフレビューで通してください' not in prompt
    assert command(response(record))['status'] == 'passed'
    bad = copy.deepcopy(m); bad['assurance']['adequate_oracle'] = False
    context = state.load_context(cp)
    context['execution']['gates']['assurance_contract'] = e.assurance_contract(bad)
    with pytest.raises(e.EvidenceError, match='adequate oracle'):
        e.validate_assurance_contract(context, bad, complete=True)


@pytest.mark.parametrize('case', ['valid', 'old_run', 'skipped', 'failed', 'zero_targets'])
def test_direct_pytest_reparses_raw_report(change, case):
    op = direct_v2(change)
    source = 'def test_x():\n    assert True\n'
    if case == 'skipped': source = 'import pytest\ndef test_x():\n    pytest.skip("skip")\n'
    if case == 'failed': source = 'def test_x():\n    assert False\n'
    (change['repo'] / 'test_x.py').write_text(source)
    op['target']['allowlist']['paths'].append('test_x.py')
    definition = copy.deepcopy(change['collect']['definition'])
    definition.update(kind='pytest', argv=[sys.executable, '-m', 'pytest', 'test_x.py::test_x'],
                      targets=['test_x.py::test_x'], assertions=[])
    definition['inputs'].append(ref('repo', 'test_x.py', change['repo']))
    if case == 'zero_targets': definition['argv'] += ['-k', 'never_matches']
    change['collect']['definition'] = definition
    collected = hr.collect_direct(change['path'], change['collect'])
    if case == 'old_run': hr.collect_direct(change['path'], change['collect'])
    op['quality']['validation']['checks'] = [dict(definition=definition, receipt=collected['receipt'])]
    snapshot = hr._snapshot_target(op['scope'], op['target'])
    for row in op['quality']['reviews']: row['snapshot_id'] = snapshot['snapshot_id']
    result = cli(change, op, 0)
    assert (result.returncode == 0) == (case == 'valid'), result.stderr


def test_direct_v2_cannot_downgrade_and_raw_change_expires(change):
    op = direct_v2(change)
    assert cli(change, op, 0).returncode == 0
    record = read(change); assert record['version'] == 2
    downgraded = copy.deepcopy(op); del downgraded['scope']
    q = downgraded['quality']; del q['assurance']; del q['oracle']
    q['validation']['checks'] = [dict(id='check-1', argv=['echo', 'fixed'], status='passed',
                                    snapshot_id=q['reviews'][0]['snapshot_id'], evidence=[change['proof']])]
    assert cli(change, downgraded, 1).returncode != 0
    (direct_receipt(change).parent / 'stdout.log').write_text('mutated')
    result = cli(change)
    assert result.returncode != 0
    assert json.loads(result.stdout)['status'] == 'stale'


@pytest.mark.parametrize('case', ['snapshot', 'failure', 'interruption', 'definition', 'oracle', 'other_change'])
def test_direct_collected_receipt_cannot_be_rebound(change, monkeypatch, case):
    op = direct_v2(change)
    if case == 'snapshot':
        (change['repo'] / 'new.txt').write_text('new behavior')
        op['target']['allowlist']['paths'].append('new.txt')
        for row in op['quality']['reviews']:
            row['snapshot_id'] = hr._snapshot_target(op['scope'], op['target'])['snapshot_id']
    elif case == 'failure':
        monkeypatch.setenv('DIRECT_TEST_FAIL', '1')
        assert hr.collect_direct(change['path'], change['collect'])['status'] == 'failed'
    elif case == 'interruption':
        original = hr.evidence.subprocess.run
        def interrupt(argv, **kwargs):
            if argv == change['collect']['definition']['argv']: raise KeyboardInterrupt()
            return original(argv, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(hr.evidence.subprocess, 'run', interrupt)
            with pytest.raises(KeyboardInterrupt): hr.collect_direct(change['path'], change['collect'])
    elif case == 'definition':
        op['quality']['validation']['checks'][0]['definition']['assertions'][0]['value'] = 'weak'
    elif case == 'oracle': op['quality']['oracle']['locator'] = 'another contract'
    else:
        op['scope']['id'] = 'another-change'
        change['path'] = hr.direct_path(change['repo'], 'another-change')
    assert cli(change, op, 0).returncode != 0


def test_direct_collect_cli_rejects_caller_run_metadata(change):
    direct_v2(change)
    result = cli(change, change['collect'])
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)) == {'status', 'check_id', 'receipt'}
    for field, value in [('run_id', str(uuid.uuid4())), ('status', 'passed'), ('snapshot_id', 'sha256:' + '0' * 64)]:
        forged = dict(change['collect'], **{field: value})
        assert cli(change, forged).returncode != 0


def test_low_export_retains_auto_pass_and_detects_raw_tampering(gate, tmp_path):
    e, state, repo, cp, m, _ = gate
    freeze(gate); receipt = e.run_check(cp, 'command-check'); advance(state, cp, 'FINAL_REVIEW')
    assessment = dict(self_reason='既存契約を検証済み', blockers=[], cards=[], verification_assumptions=[])
    result = e.human_review_command(cp, operation=dict(action='present', assessment=assessment),
                                   expected_revision=state.load_context(cp)['state']['artifact_revision'])
    assert result['status'] == 'passed'
    output = tmp_path / 'export'
    e.export_evidence(cp, output)
    retained = e.validate_export(output)
    assert retained['human_review']['version'] == 2
    assert retained['human_review']['responses'] == []
    raw = output / 'workflow/evidence/runs' / receipt['run_id'] / 'stdout.log'
    raw.write_text('tampered')
    with pytest.raises(e.EvidenceError): e.validate_export(output)


def test_task_reentry_does_not_refreeze(gate):
    e, state, repo, cp, m, _ = gate
    freeze(gate); advance(state, cp, 'DEBUGGING')
    m['checks'][0]['assertions'][0]['value'] = 'changed'
    save(cp, m)
    with pytest.raises(state.StateError, match='E_ASSURANCE_FIXED'):
        advance(state, cp, 'TASKS')


def test_legacy_tasks_entry_keeps_incomplete_manifest_compatibility(gate):
    e, state, repo, cp, m, context = gate
    context['state']['phase'] = 'WORKTREE_READY'; cp.write_text(json.dumps(context))
    m['checks'][0]['inputs'][0]['path'] = 'not-created-yet'
    save(cp, m)
    advance(state, cp, 'TASKS')


def test_direct_important_need_rejects_unregistered_check(change):
    op = direct_v2(change)
    op['quality']['assurance']['important'] = [
        dict(id='AC1', needs=[dict(kind='negative', checks=['reject-invalid'])])]
    result = cli(change, op, 0)
    assert result.returncode != 0
    assert 'need check not linked to AC' in result.stderr
    assert not change['path'].exists()


def test_direct_important_needs_share_one_measured_check(change):
    op = direct_v2(change)
    op['quality']['assurance']['important'] = [
        dict(id=aid, needs=[dict(kind=kind, checks=['check-1'])
                            for kind in ('concrete', 'negative', 'invariant')])
        for aid in ('AC1', 'AC2')]
    root = hr._direct_root(op['scope'])
    before = hr.evidence._starts(root)
    assert len(before) == 1
    result = cli(change, op, 0)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'passed'
    assert cli(change).returncode == 0
    assert hr.evidence._starts(root) == before


@pytest.mark.parametrize('risk_kind', ['concurrency', 'persistence', 'integration'])
def test_medium_requires_only_selected_risk_checks(gate, risk_kind):
    """risk別checkの選択と実行gateを検証する。各領域の挙動検証ではない。"""
    e, state, repo, cp, m, context = gate
    candidates = {}
    for kind in ('concurrency', 'persistence', 'integration'):
        check = copy.deepcopy(m['checks'][0])
        check.update(id=kind + '-check', argv=[sys.executable, '-c', f'print({kind!r})'],
                     assertions=[dict(stream='stdout', op='equals', value=kind + '\n')])
        candidates[kind] = check
    selected = candidates[risk_kind]
    unrelated = {check['id'] for kind, check in candidates.items() if kind != risk_kind}
    m.update(version=2, assurance=assurance('medium'))
    m['assurance']['risks'] = [dict(kind=risk_kind, checks=[selected['id']])]
    m['checks'].append(selected)
    m['active'][0]['checks'].append(selected['id'])
    m['review']['ac'][0]['checks'].append(selected['id'])
    save(cp, m)
    context['state']['phase'] = 'WORKTREE_READY'
    cp.write_text(json.dumps(context))
    advance(state, cp, 'TASKS')
    m['review']['reviewed_contract_hash'] = e.contract_hash(m)
    save(cp, m)
    common_receipt = e.run_check(cp, 'command-check')
    advance(state, cp, 'FINAL_REVIEW')
    advance(state, cp, 'LOCAL_VERIFICATION')
    before = cp.read_bytes()
    with pytest.raises(state.StateError, match='no attempt for ' + selected['id']):
        advance(state, cp, 'LOCAL_COMPLETE')
    assert cp.read_bytes() == before
    assert [start['check_ids'] for _, start in e._starts(cp.parent)] == [['command-check']]
    selected_receipt = e.run_check(cp, selected['id'])
    grant_consent(e, state, cp)
    completed = advance(state, cp, 'LOCAL_COMPLETE')
    assert set(completed['execution']['gates']['local_verification']['run_ids']) == {
        common_receipt['run_id'], selected_receipt['run_id']}
    required = {check['id'] for check in e.load_contract(cp)['checks']}
    executed = {identifier for _, start in e._starts(cp.parent) for identifier in start['check_ids']}
    assert required == executed == {'command-check', selected['id']}
    assert not unrelated & (required | executed)
