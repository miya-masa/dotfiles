from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'dot_agents/workflows/software_delivery/scripts'
SCRIPT = SCRIPTS / 'human_review.py'
sys.path.insert(0, str(SCRIPTS))
import human_review as hr
import review_snapshot


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def change(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    (repo / 'x').write_text('base\n')
    git(repo, 'add', 'x')
    git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'base')
    target = {'base_commit': git(repo, 'rev-parse', 'HEAD'), 'allowlist': {'version': 1, 'paths': ['x']}}
    (repo / 'x').write_text('changed\n')
    record_path = hr.direct_path(repo, 'change-1')
    record_path.parent.mkdir(parents=True)

    def ref(name, text):
        (record_path.parent / name).write_text(text)
        return {'root': 'workflow', 'path': name, 'sha256': hashlib.sha256(text.encode()).hexdigest()}

    policy = dict(ref('policy.md', 'self review is enough for this change'), locator='matrix:1')
    proof = ref('proof.txt', 'test and self review passed')
    snapshot_id = review_snapshot.snapshot(repo, **{'base_commit': target['base_commit'], 'allowlist': target['allowlist']}).review_snapshot_id
    quality = {
        'kind': 'direct',
        'review_requirement': {'fresh_count': 0, 'policy': policy, 'reason': '局所的な変更'},
        'reviews': [{'id': 'self-1', 'kind': 'self', 'status': 'passed', 'snapshot_id': snapshot_id, 'evidence': [proof]}],
        'validation': {'requirement': 'required', 'reason': '変更した挙動を検証', 'evidence': [proof], 'checks': [
            {'id': 'check-1', 'argv': ['python3', '-m', 'pytest'], 'status': 'passed', 'snapshot_id': snapshot_id, 'evidence': [proof]}]},
    }
    operation = {'action': 'present', 'scope': {'id': 'change-1', 'repository': str(repo)}, 'target': target,
                 'assessment': {'self_reason': '既存規約で判断可能', 'blockers': [], 'cards': [], 'verification_assumptions': [proof]},
                 'quality': quality}
    return {'repo': repo, 'path': record_path, 'op': operation, 'proof': proof, 'tmp': tmp_path}


def cli(change, operation=None, revision=None):
    argv = [sys.executable, str(SCRIPT), '--record', str(change['path'])]
    if operation is not None:
        opfile = change['tmp'] / 'operation.json'
        opfile.write_text(json.dumps(operation))
        argv += ['--operation-file', str(opfile)]
    if revision is not None:
        argv += ['--expected-revision', str(revision)]
    return subprocess.run(argv, capture_output=True, text=True)


def read(change):
    return json.loads(change['path'].read_text())


def present(change):
    result = cli(change, change['op'], 0)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['status'] == 'pending'
    return read(change)


def response(record, targets=None, decision='approve_current'):
    return {'action': 'respond', 'presentation_id': record['presentations'][-1]['id'], 'targets': targets or ['self'],
            'decision': decision, 'user_citation': {'role': 'user', 'reference': 'conversation:turn-42', 'quote': '現在の案を承認します'}}


def approve(change):
    record = present(change)
    result = cli(change, response(record), record['revision'])
    assert result.returncode == 0, result.stderr
    return read(change)


def card(change, identifier='card-1'):
    proof = change['proof']
    return {'id': identifier, 'question': '調査時に展開したコードが必要ですか',
            'code': [{'path': 'x', 'symbol': 'process', 'excerpt': 'changed', 'reference': proof}],
            'scenario': '障害時のログから実装を追う', 'impact': '調査に必要な手順が異なる', 'evidence': [proof],
            'unresolved_reason': 'チームの障害解析手順はrepositoryにない',
            'options': [{'id': 'inline', 'description': '展開する'}, {'id': 'helper', 'description': '関数化する'}],
            'recommendation': 'inline', 'current_option': 'inline', 'answer_scope': 'processの局所的な構成だけ',
            'conditions': [{'satisfied': True, 'reason': f'条件{i}を満たす根拠', 'evidence': [proof]} for i in range(5)]}


def test_direct_completion_requires_presented_user_consent(change):
    assert cli(change).returncode != 0
    record = present(change)
    assert set(record) == {'version', 'revision', 'scope', 'presentations', 'responses'}
    prompt = record['presentations'][0]['prompt']
    for text in ('人間コードレビュー対象なし', 'セルフレビューで通してください', 'sha256:', 'proof.txt'):
        assert text in prompt
    assert cli(change).returncode == 1
    assert cli(change, response(record), 1).returncode == 0
    assert cli(change).returncode == 0


def test_minor_direct_change_still_requires_consent(change):
    present(change)
    assert cli(change).returncode == 1
    assert not (change['repo'] / '.aidocs').exists()


def test_local_cards_require_all_conditions_and_bounded_context(change):
    change['op']['assessment']['cards'] = [card(change)]
    record = present(change)
    prompt = record['presentations'][0]['prompt']
    for text in ('process', 'changed', '障害時', 'inline', 'helper', '局所的', 'sha256:'):
        assert text in prompt
    for field in ('code', 'evidence'):
        bad = copy.deepcopy(change['op']); bad.pop('scope'); bad['assessment']['cards'][0][field] = []
        before = change['path'].read_bytes()
        assert cli(change, bad, 1).returncode != 0
        assert change['path'].read_bytes() == before
    for index in range(5):
        bad = copy.deepcopy(change['op']); bad.pop('scope'); bad['assessment']['cards'][0]['conditions'][index]['satisfied'] = False
        assert cli(change, bad, 1).returncode != 0
        assert read(change) == record


def test_all_current_cards_pass_without_self_consent(change):
    change['op']['assessment']['cards'] = [card(change), card(change, 'card-2')]
    record = present(change)
    assert cli(change, response(record, ['card-1']), 1).returncode == 1
    assert cli(change).returncode == 1
    before = change['path'].read_bytes()
    assert cli(change, response(record, ['self']), 2).returncode != 0
    assert change['path'].read_bytes() == before
    assert cli(change, response(record, ['card-2']), 2).returncode == 0


def test_change_request_does_not_approve_current_implementation(change):
    record = approve(change)
    assert cli(change, response(record, decision='request_change'), 2).returncode != 0
    assert cli(change).returncode != 0


def test_assistant_or_empty_response_is_not_consent(change):
    record = present(change)
    for citation in ({}, {'role': 'assistant', 'reference': 'r', 'quote': 'ok'}, {'role': 'user', 'reference': '', 'quote': 'ok'}, {'role': 'user', 'reference': 'r', 'quote': '  '}):
        op = response(record); op['user_citation'] = citation
        before = change['path'].read_bytes()
        assert cli(change, op, 1).returncode != 0
        assert change['path'].read_bytes() == before
    assert cli(change).returncode == 1


@pytest.mark.parametrize('mutation', ['content', 'mode', 'deletion'])
def test_direct_snapshot_changes_invalidate_consent(change, mutation):
    approve(change)
    target = change['repo'] / 'x'
    if mutation == 'content': target.write_text('another change\n')
    elif mutation == 'mode': target.chmod(0o755)
    else: target.unlink()
    result = cli(change)
    assert result.returncode != 0
    assert 'E_HUMAN_REVIEW_STALE' in result.stdout + result.stderr


def test_operations_reject_missing_forbidden_or_caller_generated_fields(change):
    for field in ('basis', 'basis_hash', 'prompt', 'revision', 'presentation_id', 'ci_pending'):
        bad = copy.deepcopy(change['op']); bad[field] = 'caller supplied'
        assert cli(change, bad, 0).returncode != 0
        assert not change['path'].exists()
    bad = copy.deepcopy(change['op']); del bad['quality']
    assert cli(change, bad, 0).returncode != 0
    record = present(change)
    for field in ('basis', 'scope', 'revision'):
        op = response(record); op[field] = 'unexpected'
        before = change['path'].read_bytes()
        assert cli(change, op, 1).returncode != 0
        assert change['path'].read_bytes() == before


def test_direct_initialization_and_updates_enforce_compare_and_swap(change):
    assert cli(change, change['op']).returncode != 0
    assert not change['path'].exists()
    record = present(change)
    before = change['path'].read_bytes()
    assert cli(change, change['op'], 0).returncode != 0
    assert cli(change, response(record), 0).returncode != 0
    assert change['path'].read_bytes() == before
    assert cli(change, response(record), 1).returncode == 0
    assert read(change)['revision'] == 2


def test_direct_quality_requires_policy_review_and_applicable_validation(change):
    variants = []
    for key in ('reviews',):
        bad = copy.deepcopy(change['op']); bad['quality'][key] = []; variants.append(bad)
    for part in ('reviews', 'checks'):
        for field, value in [('status', 'failed'), ('status', 'unverified'), ('snapshot_id', 'sha256:' + '0' * 64), ('evidence', [])]:
            bad = copy.deepcopy(change['op']); rows = bad['quality']['reviews'] if part == 'reviews' else bad['quality']['validation']['checks']
            rows[0][field] = value; variants.append(bad)
    bad = copy.deepcopy(change['op']); bad['quality']['review_requirement']['fresh_count'] = 1; variants.append(bad)
    bad = copy.deepcopy(change['op']); bad['quality']['validation']['checks'] *= 2; variants.append(bad)
    bad = copy.deepcopy(change['op']); bad['quality']['validation']['requirement'] = 'not_applicable'; variants.append(bad)
    bad = copy.deepcopy(change['op']); bad['quality']['review_requirement']['policy']['sha256'] = '0' * 64; variants.append(bad)
    for op in variants:
        assert cli(change, op, 0).returncode != 0
        assert not change['path'].exists()
    approve(change)


def test_approval_updates_do_not_change_basis_hash(change):
    record = present(change)
    initial = record['presentations'][0]['basis_hash']
    assert cli(change, response(record), 1).returncode == 0
    assert read(change)['presentations'][0]['basis_hash'] == initial
    assert cli(change).returncode == 0


@pytest.mark.parametrize('mutation', ['tamper', 'delete', 'symlink'])
def test_actual_reference_files_are_rechecked(change, mutation):
    record = approve(change)
    proof = change['path'].parent / 'proof.txt'
    if mutation == 'tamper': proof.write_text('failed')
    elif mutation == 'delete': proof.unlink()
    else:
        proof.unlink(); proof.symlink_to(change['repo'] / 'x')
    before = change['path'].read_bytes()
    assert cli(change).returncode != 0
    assert cli(change, response(record), 2).returncode != 0
    assert change['path'].read_bytes() == before


def test_revocation_requires_new_presentation(change):
    record = approve(change)
    revoke = response(record); revoke['action'] = 'revoke'; revoke.pop('decision')
    assert cli(change, revoke, 2).returncode != 0
    assert read(change)['responses'][-1]['action'] == 'revoke'
    assert cli(change, response(record), 3).returncode != 0
    op = copy.deepcopy(change['op']); op.pop('scope')
    assert cli(change, op, read(change)['revision']).returncode == 1
    fresh = read(change)
    assert fresh['presentations'][-1]['id'] != record['presentations'][-1]['id']
    before = change['path'].read_bytes()
    assert cli(change, response(record), fresh['revision']).returncode != 0
    assert change['path'].read_bytes() == before
    assert cli(change, response(fresh), fresh['revision']).returncode == 0


def test_invalid_location_duplicate_keys_and_schema_do_not_write(change):
    original = change['path']; change['path'] = change['tmp'] / 'wrong.json'
    assert cli(change, change['op'], 0).returncode != 0
    assert not change['path'].exists()
    change['path'] = original
    present(change)
    for mutate in (lambda r: r.update(parent='bad'), lambda r: r.update(revision=True),
                   lambda r: r['presentations'][0].update(id='not-a-uuid')):
        record = read(change); mutate(record); original.write_text(json.dumps(record))
        before = original.read_bytes()
        assert cli(change).returncode != 0
        assert original.read_bytes() == before
        original.unlink(); present(change)
    original.write_text(original.read_text().replace('"version": 1', '"version": 1, "version": 1'))
    assert cli(change).returncode != 0


@pytest.mark.parametrize('kind,route', [('bug', 'fix'), ('test_gap', 'verify'), ('environment', 'verify'), ('specification', 'specification'), ('technical_disagreement', 'diagnose')])
def test_blockers_cannot_be_presented_for_consent(change, kind, route):
    change['op']['assessment']['blockers'] = [{'kind': kind, 'reason': '未解決', 'evidence': [change['proof']]}]
    assert hr.classify_assessment(change['op']['assessment']) == route
    assert cli(change, change['op'], 0).returncode != 0
    assert not change['path'].exists()


def test_concurrent_direct_initialization_has_one_winner(change):
    opfile = change['tmp'] / 'initial.json'
    opfile.write_text(json.dumps(change['op']))
    argv = [sys.executable, str(SCRIPT), '--record', str(change['path']), '--operation-file', str(opfile), '--expected-revision', '0']
    processes = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [p.communicate(timeout=10) for p in processes]
    assert sorted(p.returncode for p in processes) == [1, 2], results
    record = read(change)
    assert record['revision'] == 1 and len(record['presentations']) == 1


@pytest.mark.parametrize('field', ['base_commit', 'allowlist'])
def test_representing_changed_target_requires_new_consent(change, field):
    old = approve(change)
    op = copy.deepcopy(change['op']); op.pop('scope')
    if field == 'base_commit':
        git(change['repo'], 'add', 'x')
        git(change['repo'], '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'new base')
        op['target']['base_commit'] = git(change['repo'], 'rev-parse', 'HEAD')
    else:
        (change['repo'] / 'y').write_text('dependency')
        op['target']['allowlist']['paths'].append('y')
    snapshot_id = review_snapshot.snapshot(change['repo'], op['target']['base_commit'], op['target']['allowlist']).review_snapshot_id
    for row in op['quality']['reviews'] + op['quality']['validation']['checks']:
        row['snapshot_id'] = snapshot_id
    assert cli(change, op, 2).returncode == 1
    new = read(change)
    assert new['presentations'][-1]['basis_hash'] != old['presentations'][-1]['basis_hash']
    assert cli(change).returncode == 1
    assert cli(change, response(new), 3).returncode == 0


@pytest.mark.parametrize('count', [1, 2])
def test_required_fresh_reviews_are_preserved(change, count):
    quality = change['op']['quality']
    quality['review_requirement']['fresh_count'] = count
    quality['reviews'] = [{**quality['reviews'][0], 'id': f'fresh-{i}', 'kind': 'fresh'} for i in range(count)]
    approve(change)


def test_not_applicable_requires_auditable_reason(change):
    validation = change['op']['quality']['validation']
    validation.update(requirement='not_applicable', reason='実行対象validationがない設定外資料', checks=[])
    bad = copy.deepcopy(change['op']); bad['quality']['validation']['evidence'] = []
    assert cli(change, bad, 0).returncode != 0
    approve(change)


def test_workflow_basis_protocol_rechecks_refs_and_changes(change):
    """T2 still owns review/receipt semantics; this exercises the shared boundary."""
    direct = change['op']
    target = dict(direct['target'], snapshot_id=direct['quality']['reviews'][0]['snapshot_id'])
    quality = {'kind': 'workflow', 'contract_hash': 'sha256:' + 'a' * 64, 'review': {},
               'local_receipts': [{'check_id': 'local-1', 'receipt': change['proof']}]}
    root = change['path'].parent
    basis, _ = hr.build_basis(direct['scope'], target, direct['assessment'], quality, workflow_root=root)
    record = hr.apply_operation(None, {'action': 'present', 'assessment': direct['assessment']},
                                expected_revision=0, workflow_root=root, current_basis=basis, ci_pending=True)
    assert 'CI未完' in record['presentations'][0]['prompt']
    record = hr.apply_operation(record, response(record), expected_revision=1, workflow_root=root, current_basis=basis)
    assert hr.evaluate_human_review(record, workflow_root=root, current_basis=basis)['status'] == 'passed'
    assert hr.evaluate_human_review(record, workflow_root=root)['status'] == 'blocked'
    changed = copy.deepcopy(basis); changed['quality']['contract_hash'] = 'sha256:' + 'b' * 64
    assert hr.evaluate_human_review(record, workflow_root=root, current_basis=changed)['status'] == 'stale'
    (root / 'proof.txt').write_text('changed proof')
    assert hr.evaluate_human_review(record, workflow_root=root, current_basis=basis)['status'] == 'stale'


def test_direct_basis_rejects_ci_history_and_unsafe_refs(change):
    op = change['op']
    target = dict(op['target'], snapshot_id=op['quality']['reviews'][0]['snapshot_id'])
    with pytest.raises(hr.HumanReviewError):
        hr.build_basis(op['scope'], target, op['assessment'], op['quality'], workflow_root=change['path'].parent,
                       ci_history=[{'check_id': 'ci', 'start': change['proof'], 'receipt': change['proof'], 'successor_start': None}])
    for path in ('../proof.txt', '/etc/passwd', 'nested/../proof.txt'):
        bad = copy.deepcopy(op); bad['assessment']['verification_assumptions'][0]['path'] = path
        assert cli(change, bad, 0).returncode != 0
        assert not change['path'].exists()


def test_strict_record_rejects_unknown_cards_duplicate_ids_and_basis_tampering(change):
    record = approve(change)
    mutations = [lambda r: r['presentations'].append(copy.deepcopy(r['presentations'][0])),
                 lambda r: r['responses'][0].update(targets=['unknown']),
                 lambda r: r['responses'][0].update(action='other'),
                 lambda r: r['presentations'][0]['basis'].update(extra='forbidden'),
                 lambda r: r['presentations'][0].update(prompt='caller generated')]
    for mutate in mutations:
        bad = copy.deepcopy(record); mutate(bad)
        change['path'].write_text(json.dumps(bad))
        before = change['path'].read_bytes()
        assert cli(change).returncode != 0
        assert change['path'].read_bytes() == before


def test_malformed_operation_value_is_diagnosed_without_traceback(change):
    for key in ('quality', 'scope', 'assessment', 'target'):
        bad = copy.deepcopy(change['op']); bad[key] = []
        result = cli(change, bad, 0)
        assert result.returncode == 2
        assert 'E_HUMAN_REVIEW_SCHEMA' in result.stderr
        assert 'Traceback' not in result.stderr
        assert not change['path'].exists()


@pytest.mark.parametrize('decision', ['revoke', 'request_change'])
@pytest.mark.parametrize('invalidated', ['reference', 'code'])
def test_negative_response_persists_when_direct_basis_is_stale(change, decision, invalidated):
    record = approve(change)
    path = change['path'].parent / 'proof.txt' if invalidated == 'reference' else change['repo'] / 'x'
    original = path.read_bytes()
    if invalidated == 'reference': path.unlink()
    else: path.write_text('changed after approval')
    op = response(record, decision='request_change')
    if decision == 'revoke': op['action'] = 'revoke'; op.pop('decision')
    result = cli(change, op, 2)
    assert result.returncode == 1, result.stderr
    saved = read(change)
    assert saved['revision'] == 3
    assert saved['responses'][-1]['action'] == decision
    path.write_bytes(original)
    assert json.loads(cli(change).stdout)['status'] == 'blocked'
    before = change['path'].read_bytes()
    assert cli(change, response(saved), 3).returncode != 0
    assert change['path'].read_bytes() == before


@pytest.mark.parametrize('bad_field', ['presentation_id', 'targets', 'user_citation', 'revision'])
def test_stale_direct_negative_response_still_checks_identity_citation_and_cas(change, bad_field):
    record = approve(change)
    (change['path'].parent / 'proof.txt').unlink()
    op = response(record); op['action'] = 'revoke'; op.pop('decision')
    revision = 2
    if bad_field == 'presentation_id': op['presentation_id'] = '00000000-0000-0000-0000-000000000000'
    elif bad_field == 'targets': op['targets'] = ['unknown']
    elif bad_field == 'user_citation': op['user_citation']['role'] = 'assistant'
    else: revision = 1
    before = change['path'].read_bytes()
    assert cli(change, op, revision).returncode == 2
    assert change['path'].read_bytes() == before
