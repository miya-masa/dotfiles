#!/usr/bin/env python3
"""Bounded human-review records; direct CLI and unlocked workflow primitives.

Workflow callers supply current_basis only after validating the existing local
receipts, AI review and CI history. This module checks their shape/references;
it does not replace those validators or confer shipping authorization.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import uuid


def _sibling(name):
    module_name = '_human_review_' + name
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name(name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return sys.modules[module_name]


evidence = _sibling('workflow_evidence')
snapshots = _sibling('review_snapshot')


class HumanReviewError(ValueError):
    def __init__(self, message, code='E_HUMAN_REVIEW_SCHEMA'):
        self.code = code
        super().__init__(f'{code}: {message}')


def _keys(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise HumanReviewError(f'invalid {label} keys')


def _string(value, label):
    if not isinstance(value, str) or not value.strip() or '\0' in value:
        raise HumanReviewError(f'{label} must be a nonempty string')


def _array(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise HumanReviewError(f'{label} must be an array' + (' with entries' if nonempty else ''))


def _hash(value, label, prefix=True):
    if not isinstance(value, str) or not re.fullmatch(('sha256:' if prefix else '') + '[0-9a-f]{64}', value):
        raise HumanReviewError(f'invalid {label}')


def _sha(value):
    return 'sha256:' + hashlib.sha256(evidence._canonical(value)).hexdigest()


def _ref(value, label, oracle=False):
    try:
        evidence._ref_shape(value, label, oracle=oracle)
    except evidence.EvidenceError as exc:
        raise HumanReviewError(str(exc)) from exc


def _refs(value, label, nonempty=True):
    _array(value, label, nonempty)
    for ref in value:
        _ref(ref, label)


def _scope(value):
    _keys(value, 'id repository', 'scope')
    _string(value['id'], 'scope.id')
    if value['id'] in {'.', '..'} or '/' in value['id'] or '\\' in value['id']:
        raise HumanReviewError('invalid scope.id')
    _string(value['repository'], 'scope.repository')
    if not Path(value['repository']).is_absolute():
        raise HumanReviewError('scope.repository must be absolute')


def _target(value, with_snapshot=True):
    _keys(value, 'base_commit allowlist' + (' snapshot_id' if with_snapshot else ''), 'target')
    if not isinstance(value['base_commit'], str) or not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', value['base_commit']):
        raise HumanReviewError('target.base_commit must be a full commit id')
    _keys(value['allowlist'], 'version paths', 'allowlist')
    try:
        snapshots.normalize_allowlist(value['allowlist'])
    except snapshots.SnapshotError as exc:
        raise HumanReviewError(str(exc)) from exc
    if with_snapshot:
        _hash(value['snapshot_id'], 'target.snapshot_id')


def validate_assessment(assessment):
    _keys(assessment, 'self_reason blockers cards verification_assumptions' + (' boundary_cards' if 'boundary_cards' in assessment else ''), 'assessment')
    _array(assessment['cards'], 'cards')
    if assessment['cards']:
        if not isinstance(assessment['self_reason'], str):
            raise HumanReviewError('self_reason must be a string')
    else:
        _string(assessment['self_reason'], 'self_reason')
    _array(assessment['blockers'], 'blockers')
    for blocker in assessment['blockers']:
        _keys(blocker, 'kind reason evidence', 'blocker')
        if blocker['kind'] not in ('bug', 'test_gap', 'environment', 'specification', 'technical_disagreement'):
            raise HumanReviewError('unknown blocker kind')
        _string(blocker['reason'], 'blocker.reason')
        _refs(blocker['evidence'], 'blocker.evidence')
    _refs(assessment['verification_assumptions'], 'verification_assumptions', nonempty=False)
    ids = set()
    for card in assessment['cards']:
        _keys(card, 'id question code scenario impact evidence unresolved_reason options recommendation current_option answer_scope conditions', 'card')
        for key in ('id', 'question', 'scenario', 'impact', 'unresolved_reason', 'recommendation', 'current_option', 'answer_scope'):
            _string(card[key], 'card.' + key)
        if card['id'] in ids or card['id'] == 'self':
            raise HumanReviewError('duplicate or reserved card id')
        ids.add(card['id'])
        _array(card['code'], 'card.code', True)
        for code in card['code']:
            _keys(code, 'path symbol excerpt reference', 'code')
            for key in ('path', 'symbol', 'excerpt'):
                _string(code[key], 'code.' + key)
            try:
                evidence._relative(code['path'], 'code.path')
            except evidence.EvidenceError as exc:
                raise HumanReviewError(str(exc)) from exc
            _ref(code['reference'], 'code.reference')
        _refs(card['evidence'], 'card.evidence')
        _array(card['options'], 'options')
        if len(card['options']) < 2:
            raise HumanReviewError('at least two options required')
        option_ids = set()
        for option in card['options']:
            _keys(option, 'id description', 'option')
            _string(option['id'], 'option.id')
            _string(option['description'], 'option.description')
            if option['id'] in option_ids:
                raise HumanReviewError('duplicate option')
            option_ids.add(option['id'])
        if card['recommendation'] not in option_ids or card['current_option'] not in option_ids:
            raise HumanReviewError('unknown option reference')
        _array(card['conditions'], 'conditions')
        if len(card['conditions']) != 5:
            raise HumanReviewError('five ordered conditions required')
        for condition in card['conditions']:
            _keys(condition, 'satisfied reason evidence', 'condition')
            if condition['satisfied'] is not True:
                raise HumanReviewError('all five human-review conditions must be satisfied')
            _string(condition['reason'], 'condition.reason')
            _refs(condition['evidence'], 'condition.evidence')

    _array(assessment.get('boundary_cards', []), 'boundary_cards')
    for card in assessment.get('boundary_cards', []):
        _keys(card, 'id boundary question code scenario impact evidence answer_scope', 'boundary card')
        for key in ('id', 'boundary', 'question', 'scenario', 'impact', 'answer_scope'):
            _string(card[key], 'boundary card.' + key)
        if card['id'] in ids or card['id'] == 'self':
            raise HumanReviewError('duplicate or reserved card id')
        ids.add(card['id'])
        _array(card['code'], 'boundary code', True)
        for code in card['code']:
            _keys(code, 'path symbol excerpt reference', 'code')
            for key in ('path', 'symbol', 'excerpt'):
                _string(code[key], 'code.' + key)
            try:
                evidence._relative(code['path'], 'code.path')
            except evidence.EvidenceError as exc:
                raise HumanReviewError(str(exc)) from exc
            _ref(code['reference'], 'code.reference')
        _refs(card['evidence'], 'boundary evidence')


def classify_assessment(assessment):
    """Classify Controller-assessed facts; do not infer human need from risk."""
    validate_assessment(assessment)
    routes = {'bug': 'fix', 'test_gap': 'verify', 'environment': 'verify',
              'specification': 'specification', 'technical_disagreement': 'diagnose'}
    if assessment['blockers']:
        return routes[assessment['blockers'][0]['kind']]
    return 'human' if assessment['cards'] or assessment.get('boundary_cards') else 'self'


def validate_quality(quality, snapshot_id=None):
    if not isinstance(quality, dict):
        raise HumanReviewError('quality must be an object')
    if quality.get('kind') == 'workflow':
        _keys(quality, 'kind contract_hash review local_receipts' + (' assurance assurance_contract' if 'assurance' in quality else ''), 'workflow quality')
        _hash(quality['contract_hash'], 'contract_hash')
        if 'assurance' in quality:
            _keys(quality['assurance_contract'], 'projection_hash', 'assurance contract')
            _hash(quality['assurance_contract']['projection_hash'], 'assurance projection hash')
        if not isinstance(quality['review'], dict):
            raise HumanReviewError('workflow review must be an object')
        _array(quality['local_receipts'], 'local_receipts')
        ids = set()
        for row in quality['local_receipts']:
            _keys(row, 'check_id receipt', 'local receipt')
            _string(row['check_id'], 'check_id')
            if row['check_id'] in ids:
                raise HumanReviewError('duplicate local check')
            ids.add(row['check_id'])
            _ref(row['receipt'], 'receipt')
        return
    _keys(quality, 'kind review_requirement reviews validation' + (' assurance oracle' if 'assurance' in quality else ''), 'direct quality')
    if quality['kind'] != 'direct':
        raise HumanReviewError('unknown quality kind')
    requirement = quality['review_requirement']
    _keys(requirement, 'fresh_count policy reason', 'review_requirement')
    count = requirement['fresh_count']
    if type(count) is not int or count not in (0, 1, 2):
        raise HumanReviewError('fresh_count must be 0, 1 or 2')
    _ref(requirement['policy'], 'policy', oracle=True)
    _string(requirement['reason'], 'review_requirement.reason')
    _array(quality['reviews'], 'reviews')
    if len(quality['reviews']) != max(1, count):
        raise HumanReviewError('required AI reviews missing')
    validation = quality['validation']
    _keys(validation, 'requirement reason evidence checks', 'validation')
    if validation['requirement'] not in ('required', 'not_applicable'):
        raise HumanReviewError('unknown validation requirement')
    _string(validation['reason'], 'validation.reason')
    _refs(validation['evidence'], 'validation.evidence', nonempty=validation['requirement'] == 'not_applicable')
    _array(validation['checks'], 'checks')
    if bool(validation['checks']) != (validation['requirement'] == 'required'):
        raise HumanReviewError('validation checks do not match requirement')
    if 'assurance' in quality:
        ids = set()
        for row in validation['checks']:
            _keys(row, 'definition receipt', 'direct measured check')
            definition = row['definition']
            try:
                evidence._check_schema(definition, Path('.'), Path('.'), retained=True)
            except evidence.EvidenceError as exc:
                raise HumanReviewError(str(exc)) from exc
            identifier = definition['id']
            _string(identifier, 'check id')
            if identifier in ids:
                raise HumanReviewError('duplicate direct check id')
            ids.add(identifier)
            _ref(row['receipt'], 'direct receipt')
    result_checks = [] if 'assurance' in quality else validation['checks']
    for rows, review in ((quality['reviews'], True), (result_checks, False)):
        ids = set()
        for row in rows:
            _keys(row, 'id status snapshot_id evidence ' + ('kind' if review else 'argv'), 'quality result')
            _string(row['id'], 'result.id')
            if row['id'] in ids:
                raise HumanReviewError('duplicate result id')
            ids.add(row['id'])
            if row['status'] not in ('passed', 'failed', 'unverified'):
                raise HumanReviewError('unknown result status')
            _hash(row['snapshot_id'], 'result.snapshot_id')
            if snapshot_id is not None and row['snapshot_id'] != snapshot_id:
                raise HumanReviewError('result snapshot mismatch', 'E_HUMAN_REVIEW_STALE')
            _refs(row['evidence'], 'result.evidence')
            if review:
                if row['kind'] != ('fresh' if count else 'self'):
                    raise HumanReviewError('review kind does not satisfy policy')
            else:
                _array(row['argv'], 'argv', True)
                for argument in row['argv']:
                    _string(argument, 'argv item')


def _assurance_basis(basis):
    quality, assessment = basis['quality'], basis['assessment']
    a = quality.get('assurance')
    if 'assurance' not in quality:
        if 'boundary_cards' in assessment:
            raise HumanReviewError('boundary cards require assurance v2')
        return
    # Formal callers validate the actual manifest mappings before building a
    # basis. Retained shape validation still verifies the complete declaration.
    try:
        checks = {cid for row in a.get('risks', []) for cid in row.get('checks', [])}
        active = []
        for item in a.get('important', []):
            ids = {cid for need in item.get('needs', []) for cid in need.get('checks', [])}
            checks |= ids
            active.append(dict(id=item.get('id'), checks=list(ids)))
        definitions = [dict(id=cid) for cid in checks]
        if quality['kind'] == 'direct':
            definitions = [row['definition'] for row in quality['validation']['checks']]
            measured = {definition['id'] for definition in definitions}
            for entry in active:
                entry['checks'] = sorted(set(entry['checks']) & measured)
        evidence.validate_assurance(a, active, definitions)
    except (evidence.EvidenceError, TypeError, AttributeError) as exc:
        raise HumanReviewError(str(exc)) from exc
    if not a['adequate_oracle']:
        raise HumanReviewError('adequate oracle required', 'E_HUMAN_REVIEW_REQUIRED')
    boundaries = {c['boundary'] for c in assessment.get('boundary_cards', [])}
    if a['risk'] == 'high' and boundaries != set(a['protected_boundaries']):
        raise HumanReviewError('HIGH requires every declared boundary card')
    if a['risk'] != 'high' and boundaries:
        raise HumanReviewError('boundary cards require HIGH')
    if quality['kind'] == 'direct':
        if a['risk'] != 'low':
            raise HumanReviewError('v2 direct route is limited to LOW; use formal workflow')
        _ref(quality['oracle'], 'preexisting oracle', oracle=True)
        if quality['oracle']['root'] != 'repo':
            raise HumanReviewError('direct LOW oracle must be in repository')
        if quality['validation']['requirement'] != 'required':
            raise HumanReviewError('direct LOW requires raw validation')


def _direct_manifest(scope, target, oracle, definition):
    return dict(workflow_id='direct:' + scope['id'], scope=scope,
                target={k: target[k] for k in ('base_commit', 'allowlist')},
                allowlist=target['allowlist'], oracle=oracle, checks=[definition])


def _direct_root(scope):
    return direct_path(scope['repository'], scope['id']).parent / 'runs' / scope['id']


def _direct_definition(definition, repo, root):
    try:
        evidence._check_schema(definition, root, repo)
        evidence._ids([definition], r'[a-z][a-z0-9_-]*', 'direct check', nonempty=True)
    except evidence.EvidenceError as exc:
        raise HumanReviewError(str(exc)) from exc
    if definition['kind'] == 'gitlab_ci' or any(ref['root'] != 'repo' for ref in definition['inputs']):
        raise HumanReviewError('direct checks require local commands and repository inputs')


def _direct_oracle(scope, target, oracle):
    _ref(oracle, 'preexisting oracle', oracle=True)
    if oracle['root'] != 'repo':
        raise HumanReviewError('direct LOW oracle must be in repository')
    repo = Path(scope['repository'])
    try:
        evidence._ref(repo, oracle, 'preexisting oracle', oracle=True)
    except evidence.EvidenceError as exc:
        raise HumanReviewError(str(exc), 'E_HUMAN_REVIEW_STALE') from exc
    result = subprocess.run(['git', '-C', str(repo), 'show', target['base_commit'] + ':' + oracle['path']], capture_output=True)
    if result.returncode or hashlib.sha256(result.stdout).hexdigest() != oracle['sha256']:
        raise HumanReviewError('LOW oracle must already exist unchanged at base commit', 'E_HUMAN_REVIEW_STALE')


def collect_direct(path, operation):
    """Use the shared execution collector; callers cannot supply run identity."""
    _keys(operation, 'action scope target oracle definition', 'direct collect')
    if operation['action'] != 'collect':
        raise HumanReviewError('collect action required')
    scope, target = operation['scope'], operation['target']
    _safe_record_path(path, scope)
    with _record_lock(path):
        _snapshot_target(scope, target)
        _direct_oracle(scope, target, operation['oracle'])
        root, repo = _direct_root(scope), Path(scope['repository'])
        _direct_definition(operation['definition'], repo, root)
        for component in (root, *root.parents):
            if component.is_symlink():
                raise HumanReviewError('direct execution root must not contain symlinks')
        root.mkdir(parents=True, exist_ok=True)
        manifest = _direct_manifest(scope, target, operation['oracle'], operation['definition'])
        try:
            receipt = evidence.run_local_check(root, repo, dict(identity=dict(base_commit=target['base_commit'])), manifest, operation['definition'])
        except evidence.EvidenceError as exc:
            raise HumanReviewError(str(exc), 'E_HUMAN_REVIEW_REQUIRED') from exc
        selected = root / 'evidence' / 'runs' / receipt['run_id'] / 'receipt.json'
        return dict(status=receipt['results'][0]['status'], check_id=operation['definition']['id'],
                    receipt=evidence._file_ref(path.parent, selected))


def _direct_raw(basis, workflow_root):
    quality = basis['quality']
    if quality['kind'] != 'direct' or 'assurance' not in quality:
        return
    scope, target = basis['scope'], basis['target']
    repo, root = Path(scope['repository']), _direct_root(scope)
    _direct_oracle(scope, target, quality['oracle'])
    for row in quality['validation']['checks']:
        check = row['definition']
        _direct_definition(check, repo, root)
        manifest = _direct_manifest(scope, target, quality['oracle'], check)
        try:
            directory, start = evidence.latest_start(root / 'context.json', manifest, check['id'], target['snapshot_id'])
            selected = evidence._ref(Path(workflow_root), row['receipt'], 'direct receipt')
            if row['receipt']['root'] != 'workflow' or selected != directory / 'receipt.json':
                raise HumanReviewError('direct receipt is not the latest attempt for this change', 'E_HUMAN_REVIEW_STALE')
            receipt = evidence.validate_receipt(root, manifest, check, directory, start)
            if evidence._input_hashes(root, repo, check) != receipt['inputs_after']:
                raise HumanReviewError('direct inputs differ from receipt', 'E_HUMAN_REVIEW_STALE')
        except (evidence.EvidenceError, OSError) as exc:
            raise HumanReviewError(str(exc), 'E_HUMAN_REVIEW_STALE') from exc


def _quality_ready(quality):
    if quality['kind'] == 'direct':
        checks = [] if 'assurance' in quality else quality['validation']['checks']
        for row in quality['reviews'] + checks:
            if row['status'] != 'passed':
                raise HumanReviewError('required review/validation has not passed', 'E_HUMAN_REVIEW_REQUIRED')


def _basis_shape(basis):
    _keys(basis, 'scope target assessment quality ci_history', 'basis')
    _scope(basis['scope'])
    _target(basis['target'])
    validate_assessment(basis['assessment'])
    validate_quality(basis['quality'], basis['target']['snapshot_id'])
    _assurance_basis(basis)
    _array(basis['ci_history'], 'ci_history')
    if basis['quality']['kind'] == 'direct' and basis['ci_history']:
        raise HumanReviewError('direct CI history must be empty')
    for row in basis['ci_history']:
        _keys(row, 'check_id start receipt successor_start', 'CI history')
        _string(row['check_id'], 'CI check_id')
        _ref(row['start'], 'CI start')
        if (row['receipt'] is None) == (row['successor_start'] is None):
            raise HumanReviewError('CI history requires failure receipt or successor')
        for field in ('receipt', 'successor_start'):
            if row[field] is not None:
                _ref(row[field], 'CI ' + field)


def iter_references(value):
    """Yield nested Ref/Oracle objects, including workflow review references."""
    if isinstance(value, dict):
        if {'root', 'path', 'sha256'} <= value.keys():
            _ref(value, 'basis reference', oracle='locator' in value)
            yield value
        else:
            for child in value.values():
                yield from iter_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_references(child)


def _verify_references(basis, workflow_root, reference_roots=None):
    roots = {'repo': Path(basis['scope']['repository']), 'workflow': Path(workflow_root)}
    if reference_roots is not None:
        _keys(reference_roots, 'repo workflow', 'reference roots')
        roots = {key: Path(value) for key, value in reference_roots.items()}
    for ref in iter_references(basis):
        try:
            evidence._ref(roots[ref['root']], ref, 'human review reference', oracle='locator' in ref)
        except (evidence.EvidenceError, OSError) as exc:
            raise HumanReviewError(str(exc), 'E_HUMAN_REVIEW_STALE') from exc


def build_basis(scope, target, assessment, quality, *, workflow_root, ci_history=None, reference_roots=None):
    """Build a hash after checking schema and actual reference bytes.

For workflow quality, the caller must first run the existing review/receipt/CI
validators. target includes the snapshot ID generated by the shared snapshot.
"""
    basis = copy.deepcopy(dict(scope=scope, target=target, assessment=assessment,
                               quality=quality, ci_history=[] if ci_history is None else ci_history))
    _basis_shape(basis)
    _verify_references(basis, workflow_root, reference_roots)
    _direct_raw(basis, workflow_root)
    return basis, _sha(basis)


def _citation(citation):
    _keys(citation, 'role reference quote', 'user_citation')
    if citation['role'] != 'user':
        raise HumanReviewError('citation must have user role', 'E_HUMAN_REVIEW_RESPONSE')
    _string(citation['reference'], 'citation.reference')
    _string(citation['quote'], 'citation.quote')


def validate_response(response):
    _keys(response, 'presentation_id targets action user_citation', 'response')
    _uuid(response['presentation_id'])
    _array(response['targets'], 'targets', True)
    for target in response['targets']:
        _string(target, 'target')
    if len(set(response['targets'])) != len(response['targets']):
        raise HumanReviewError('duplicate response target')
    if response['action'] not in ('approve_current', 'request_change', 'revoke'):
        raise HumanReviewError('unknown response action')
    _citation(response['user_citation'])


def _uuid(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError()
    except ValueError as exc:
        raise HumanReviewError('invalid presentation UUID') from exc


def _targets(presentation):
    return {c['id'] for c in presentation['assessment']['cards'] + presentation['assessment'].get('boundary_cards', [])} or {'self'}


def validate_record_shape(record):
    """Pure shape/internal consistency validation, without reading live roots."""
    _keys(record, 'version revision scope presentations responses', 'record')
    if type(record['version']) is not int or record['version'] not in (1, 2) or type(record['revision']) is not int or record['revision'] < 0:
        raise HumanReviewError('invalid record version/revision')
    _scope(record['scope'])
    _array(record['presentations'], 'presentations')
    _array(record['responses'], 'responses')
    presentations = {}
    seen_v2 = False
    for p in record['presentations']:
        _keys(p, 'id target basis_hash basis assessment ci_pending prompt', 'presentation')
        _uuid(p['id'])
        if p['id'] in presentations:
            raise HumanReviewError('presentation ID reused')
        presentations[p['id']] = p
        _basis_shape(p['basis'])
        v2 = 'assurance' in p['basis']['quality']
        if (v2 and record['version'] != 2) or (seen_v2 and not v2):
            raise HumanReviewError('assurance record version mismatch or downgrade')
        seen_v2 = seen_v2 or v2
        if p['basis_hash'] != _sha(p['basis']):
            raise HumanReviewError('basis hash mismatch')
        if p['target'] != p['basis']['target'] or p['assessment'] != p['basis']['assessment'] or record['scope'] != p['basis']['scope']:
            raise HumanReviewError('presentation differs from basis')
        if type(p['ci_pending']) is not bool or (p['basis']['quality']['kind'] == 'direct' and p['ci_pending']):
            raise HumanReviewError('invalid ci_pending')
        _string(p['prompt'], 'prompt')
        if p['prompt'] != render_prompt(p['basis'], ci_pending=p['ci_pending']):
            raise HumanReviewError('presentation prompt differs from basis')
    if record['version'] == 2 and record['presentations'] and not seen_v2:
        raise HumanReviewError('v2 record requires assurance')
    previous_index = -1
    order = {pid: index for index, pid in enumerate(presentations)}
    for response in record['responses']:
        validate_response(response)
        pid = response['presentation_id']
        if pid not in presentations or not set(response['targets']) <= _targets(presentations[pid]):
            raise HumanReviewError('response references unknown presentation/card')
        if order[pid] < previous_index:
            raise HumanReviewError('response order returns to an old presentation')
        previous_index = order[pid]


def render_prompt(basis, *, ci_pending=False):
    assessment, quality = basis['assessment'], basis['quality']
    lines = [f"対象: {basis['scope']['id']} / {basis['target']['snapshot_id']}"]
    if assessment.get('boundary_cards'):
        lines.append('境界レビュー: 各境界の現在の実装への承認をお願いします。')
        for card in assessment['boundary_cards']:
            lines += [f"[{card['id']}] {card['boundary']}: {card['question']}"]
            for code in card['code']:
                lines += [f"{code['path']} / {code['symbol']}", code['excerpt']]
            lines += [f"シナリオ: {card['scenario']}", f"影響: {card['impact']}", f"回答の効力: {card['answer_scope']}"]
    if assessment['cards']:
        lines.append('人間コードレビュー: 各カードの現在の実装案への承認をお願いします。')
        for card in assessment['cards']:
            lines += [f"[{card['id']}] {card['question']}"]
            for code in card['code']:
                lines += [f"{code['path']} / {code['symbol']} ({code['reference']['root']}:{code['reference']['path']})", code['excerpt']]
            lines += [f"シナリオ: {card['scenario']}", f"影響: {card['impact']}",
                      f"AIで決められない理由: {card['unresolved_reason']}"]
            lines += [f"選択肢 {o['id']}: {o['description']}" for o in card['options']]
            lines += [f"推奨: {card['recommendation']} / 現在の実装: {card['current_option']}",
                      f"回答の効力: {card['answer_scope']}"]
    elif quality.get('assurance', {}).get('risk') == 'low':
        lines += ['LOW: 検証済みの現在の対象を自動通過します。回答は不要です。', f"変更と判断根拠: {assessment['self_reason']}"]
    elif quality.get('assurance', {}).get('risk') == 'medium':
        lines += ['MEDIUM: 変更挙動・重要な証跡・残余リスクを確認してください。全diffの精読は不要です。',
                  f"変更と判断根拠: {assessment['self_reason']}",
                  'この挙動・検証前提でよければ「現在の案を承認します」と回答してください。']
    elif not assessment.get('boundary_cards'):
        lines += ['人間コードレビュー対象なし。', f"理由: {assessment['self_reason']}",
                  'セルフレビューで通してよければ「セルフレビューで通してください」と承認してください。']
    if quality['kind'] == 'direct':
        lines.append('必要なAIレビュー: ' + ', '.join(f"{r['id']} ({r['kind']}): {r['status']}" for r in quality['reviews']))
        validation = quality['validation']
        lines.append('テスト: ' + (', '.join((f"{c['definition']['id']}: receipt検証済み" if 'assurance' in quality else f"{c['id']}: {c['status']}") for c in validation['checks']) or f"対象なし ({validation['reason']})"))
    else:
        lines += ['必要なAIレビュー: 検査済みのmanifest.reviewを参照。',
                  'local検証: ' + ', '.join(r['check_id'] for r in quality['local_receipts'])]
    refs = sorted({f"{r['root']}:{r['path']} ({r['sha256']})" for r in iter_references(basis)})
    lines.append('証跡: ' + ', '.join(refs))
    if ci_pending:
        lines.append('CI未完: 承認済みのCI委譲が残っています。')
    lines.append('承認の効力は現在のコードレビューgateに限定され、shipping認可を含みません。')
    return '\n'.join(lines)


def _snapshot_target(scope, target):
    _scope(scope)
    _target(target, with_snapshot=False)
    try:
        root = snapshots.repository_root(scope['repository'])
        if root != Path(scope['repository']):
            raise HumanReviewError('scope.repository must be the canonical Git root')
        result = snapshots.snapshot(root, target['base_commit'], target['allowlist'])
    except snapshots.SnapshotError as exc:
        raise HumanReviewError(str(exc), 'E_HUMAN_REVIEW_STALE') from exc
    return {**copy.deepcopy(target), 'snapshot_id': result.review_snapshot_id}


def _current_basis(record, workflow_root, current_basis, reference_roots=None):
    p = record['presentations'][-1]
    old = p['basis']
    if old['quality']['kind'] == 'direct':
        target = _snapshot_target(record['scope'], {k: p['target'][k] for k in ('base_commit', 'allowlist')})
        basis, _ = build_basis(record['scope'], target, p['assessment'], old['quality'], workflow_root=workflow_root)
    else:
        if current_basis is None:
            raise HumanReviewError('workflow requires freshly validated current_basis', 'E_HUMAN_REVIEW_REQUIRED')
        basis, _ = build_basis(**current_basis, workflow_root=workflow_root, reference_roots=reference_roots)
    _quality_ready(basis['quality'])
    if basis != old:
        raise HumanReviewError('current basis differs from presentation', 'E_HUMAN_REVIEW_STALE')
    return basis


def evaluate_human_review(record, *, workflow_root, current_basis=None, reference_roots=None):
    """Read-only gate. Workflow caller must pass freshly validated current_basis."""
    validate_record_shape(record)
    if not record['presentations']:
        return {'route': 'self', 'status': 'pending', 'reason': 'E_HUMAN_REVIEW_REQUIRED: presentation required', 'presentation_id': None, 'prompt': ''}
    p = record['presentations'][-1]
    result = {'route': classify_assessment(p['assessment']), 'status': 'pending',
              'presentation_id': p['id'], 'prompt': p['prompt']}
    if p['assessment']['blockers']:
        return {**result, 'status': 'blocked', 'reason': 'E_HUMAN_REVIEW_REQUIRED: unresolved blockers'}
    approved, invalidated = set(), set()
    for response in record['responses']:
        if response['presentation_id'] != p['id']:
            continue
        targets = set(response['targets'])
        if response['action'] == 'approve_current':
            approved.update(targets - invalidated)
        else:
            approved.difference_update(targets)
            invalidated.update(targets)
    missing = sorted(_targets(p) - approved)
    if invalidated:
        return {**result, 'status': 'blocked', 'reason': 'E_HUMAN_REVIEW_RESPONSE: change requested or approval revoked; new presentation required'}
    # Revocation/change requests survive missing or changed quality evidence.
    try:
        _current_basis(record, workflow_root, current_basis, reference_roots)
    except HumanReviewError as exc:
        return {**result, 'status': 'stale' if exc.code == 'E_HUMAN_REVIEW_STALE' else 'blocked', 'reason': str(exc)}
    if p['basis']['quality'].get('assurance', {}).get('risk') == 'low' and not p['assessment']['cards'] and not p['assessment'].get('boundary_cards'):
        return {**result, 'status': 'passed', 'reason': 'LOW: current quality verified; no user response required'}
    return {**result, 'status': 'pending' if missing else 'passed',
            'reason': 'E_HUMAN_REVIEW_REQUIRED: consent missing for ' + ', '.join(missing) if missing else 'approved'}


def apply_operation(record, operation, *, expected_revision, workflow_root, current_basis=None, ci_pending=False, reference_roots=None):
    """Return a validated replacement; never lock or write.

Direct present takes scope only on creation. Workflow present takes assessment
only; scope/target/quality/history come from caller-validated current_basis.
"""
    if type(expected_revision) is not int or expected_revision < 0:
        raise HumanReviewError('expected_revision must be nonnegative integer')
    if not isinstance(operation, dict):
        raise HumanReviewError('operation must be an object')
    initial = record is None
    workflow = current_basis is not None and current_basis.get('quality', {}).get('kind') == 'workflow'
    if initial:
        if operation.get('action') != 'present' or expected_revision != 0:
            raise HumanReviewError('initial record requires present at revision 0')
        scope = current_basis['scope'] if workflow else operation.get('scope')
        _scope(scope)
        record = dict(version=1, revision=0, scope=copy.deepcopy(scope), presentations=[], responses=[])
    validate_record_shape(record)
    if record['revision'] != expected_revision:
        raise HumanReviewError('stale record revision')
    result = copy.deepcopy(record)
    action = operation.get('action')
    if action == 'present':
        if workflow:
            _keys(operation, 'action assessment', 'workflow present operation')
            if current_basis['scope'] != record['scope'] or current_basis['assessment'] != operation['assessment']:
                raise HumanReviewError('workflow basis scope/assessment mismatch')
            basis, basis_hash = build_basis(**current_basis, workflow_root=workflow_root, reference_roots=reference_roots)
        else:
            _keys(operation, 'action target assessment quality' + (' scope' if initial else ''), 'direct present operation')
            if not isinstance(operation['quality'], dict) or operation['quality'].get('kind') != 'direct':
                raise HumanReviewError('workflow quality requires context validation')
            target = _snapshot_target(record['scope'], operation['target'])
            basis, basis_hash = build_basis(record['scope'], target, operation['assessment'], operation['quality'], workflow_root=workflow_root)
            if ci_pending:
                raise HumanReviewError('direct CI delegation requires formal workflow')
        _quality_ready(basis['quality'])
        route = classify_assessment(basis['assessment'])
        if route not in ('self', 'human'):
            raise HumanReviewError(f'unresolved blocker requires {route}', 'E_HUMAN_REVIEW_REQUIRED')
        if 'assurance' in basis['quality']:
            result['version'] = 2
        result['presentations'].append(dict(id=str(uuid.uuid4()), target=basis['target'], basis=basis,
                                           basis_hash=basis_hash, assessment=basis['assessment'], ci_pending=ci_pending,
                                           prompt=render_prompt(basis, ci_pending=ci_pending)))
    elif action in ('respond', 'revoke'):
        _keys(operation, 'action presentation_id targets user_citation' + (' decision' if action == 'respond' else ''), 'response operation')
        response = {key: copy.deepcopy(operation[key]) for key in ('presentation_id', 'targets', 'user_citation')}
        response['action'] = 'revoke' if action == 'revoke' else operation['decision']
        if action == 'respond' and response['action'] not in ('approve_current', 'request_change'):
            raise HumanReviewError('invalid response decision')
        validate_response(response)
        if not record['presentations'] or record['presentations'][-1]['id'] != response['presentation_id']:
            raise HumanReviewError('only latest presentation may be answered', 'E_HUMAN_REVIEW_RESPONSE')
        if not set(response['targets']) <= _targets(record['presentations'][-1]):
            raise HumanReviewError('unknown response target', 'E_HUMAN_REVIEW_RESPONSE')
        if response['action'] == 'approve_current':
            _current_basis(record, workflow_root, current_basis, reference_roots)
        if response['action'] == 'approve_current' and any(r['presentation_id'] == response['presentation_id'] and r['action'] in ('revoke', 'request_change') for r in record['responses']):
            raise HumanReviewError('new presentation required after change request/revocation', 'E_HUMAN_REVIEW_RESPONSE')
        result['responses'].append(response)
    else:
        raise HumanReviewError('unknown operation action')
    result['revision'] += 1
    validate_record_shape(result)
    return result


def direct_path(repository, change_id):
    scope = {'id': change_id, 'repository': str(Path(repository).absolute())}
    _scope(scope)
    try:
        root = snapshots.repository_root(repository)
        directory = Path(evidence._git(root, 'rev-parse', '--git-path', 'human-review'))
    except (snapshots.SnapshotError, evidence.EvidenceError) as exc:
        raise HumanReviewError(str(exc)) from exc
    return (directory if directory.is_absolute() else root / directory) / (change_id + '.json')


def _safe_record_path(path, scope):
    expected = direct_path(scope['repository'], scope['id']).absolute()
    if path.absolute() != expected:
        raise HumanReviewError('record must match repository git-path human-review/<change-id>.json')
    for component in [path, *path.parents]:
        if component.is_symlink():
            raise HumanReviewError('record path must not contain symlinks')


def _load(path):
    try:
        return evidence._json(path)
    except evidence.EvidenceError as exc:
        raise HumanReviewError(str(exc)) from exc


@contextmanager
def _record_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _write_atomic(path, record):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--context', type=Path)
    group.add_argument('--record', type=Path)
    parser.add_argument('--operation-file', type=Path)
    parser.add_argument('--expected-revision', type=int)
    args = parser.parse_args(argv)
    try:
        if args.context is not None:
            # Workflow wiring belongs to workflow_state/evidence (T2).
            adapter = _sibling('workflow_evidence')
            handler = getattr(adapter, 'human_review_command', None)
            if handler is None:
                raise HumanReviewError('workflow human-review adapter is unavailable')
            result = handler(args.context, operation=_load(args.operation_file) if args.operation_file else None,
                             expected_revision=args.expected_revision)
        else:
            path = args.record.absolute()
            if args.operation_file:
                operation = _load(args.operation_file)
                if not isinstance(operation, dict):
                    raise HumanReviewError('operation must be an object')
                if operation.get('action') == 'collect':
                    if args.expected_revision is not None:
                        raise HumanReviewError('collect does not change record revision')
                    result = collect_direct(path, operation)
                    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                    return 0 if result['status'] == 'passed' else 1
                if args.expected_revision is None:
                    raise HumanReviewError('expected-revision required for updates')
                # Check the intended metadata directory before creating/locking it.
                preliminary = _load(path) if path.exists() else None
                scope = preliminary.get('scope') if isinstance(preliminary, dict) else operation.get('scope')
                _scope(scope)
                _safe_record_path(path, scope)
                with _record_lock(path):
                    record = _load(path) if path.exists() else None
                    updated = apply_operation(record, operation, expected_revision=args.expected_revision, workflow_root=path.parent)
                    _safe_record_path(path, updated['scope'])
                    result = evaluate_human_review(updated, workflow_root=path.parent)
                    if result['status'] == 'stale':
                        raise HumanReviewError(result['reason'], 'E_HUMAN_REVIEW_STALE')
                    _write_atomic(path, updated)
            else:
                record = _load(path)
                validate_record_shape(record)
                _safe_record_path(path, record['scope'])
                result = evaluate_human_review(record, workflow_root=path.parent)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result['status'] == 'passed' else 1
    except (HumanReviewError, OSError, ValueError, TypeError) as exc:
        print(str(exc) if isinstance(exc, HumanReviewError) else f'E_HUMAN_REVIEW_SCHEMA: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
