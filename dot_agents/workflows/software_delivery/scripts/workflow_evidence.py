#!/usr/bin/env python3
"""Strict workflow contracts and local execution receipts (stdlib only).

The collector locks the workflow directory, as workflow_state does. Consumers
already inside mutate_context must use the unlocked validation primitives.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from typing import Any


class EvidenceError(ValueError):
    pass


def _fail(code, message):
    raise EvidenceError(f'{code}: {message}')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail('E_EVIDENCE_SCHEMA', f'duplicate JSON key {key}')
        result[key] = value
    return result


def _number(value):
    number = float(value)
    if not math.isfinite(number):
        _fail('E_EVIDENCE_SCHEMA', 'nonfinite JSON number')
    return number


def _decode(data):
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_float=_number, parse_constant=lambda x: _fail('E_EVIDENCE_SCHEMA', f'invalid number {x}'))
    except (ValueError, UnicodeError) as exc:
        _fail('E_EVIDENCE_SCHEMA', str(exc))


def _json(path):
    try:
        if path.is_symlink() or not path.is_file():
            _fail('E_EVIDENCE_PATH', f'not a regular file: {path}')
        return _decode(path.read_bytes())
    except OSError as exc:
        _fail('E_EVIDENCE_PATH', str(exc))


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True, allow_nan=False).encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def contract_hash(manifest):
    """Review records are deliberately outside the execution contract."""
    return 'sha256:' + _sha(_canonical({k: v for k, v in manifest.items() if k != 'review'}))


def _keys(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        _fail('E_EVIDENCE_SCHEMA', f'invalid {label} keys')


def _string(value, label):
    if not isinstance(value, str) or not value.strip() or '\0' in value:
        _fail('E_EVIDENCE_SCHEMA', f'{label} must be a nonempty string')
    return value


def _strings(value, label, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value):
        _fail('E_EVIDENCE_SCHEMA', f'{label} must be an array')
    for item in value:
        _string(item, label)
    if len(set(value)) != len(value):
        _fail('E_EVIDENCE_SCHEMA', f'duplicate {label}')
    return set(value)


def _integer(value, label, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        _fail('E_EVIDENCE_SCHEMA', f'invalid {label}')


def _relative(value, label, dot=False):
    _string(value, label)
    if dot and value == '.':
        return value
    if value.startswith('/') or '\\' in value or any(p in {'', '.', '..'} for p in value.split('/')) or str(PurePosixPath(value)) != value:
        _fail('E_EVIDENCE_PATH', f'unsafe {label}: {value}')
    return value


def _path(root, relative, label, directory=False):
    _relative(relative, label, dot=directory)
    candidate = root
    for part in PurePosixPath(relative).parts:
        candidate /= part
        if candidate.is_symlink():
            _fail('E_EVIDENCE_PATH', f'symlink in {label}')
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
        valid = candidate.is_dir() if directory else candidate.is_file()
        if not valid:
            _fail('E_EVIDENCE_PATH', f'not a regular {"directory" if directory else "file"}: {label}')
    except (OSError, ValueError) as exc:
        _fail('E_EVIDENCE_PATH', f'{label}: {exc}')
    return candidate


def _ref_shape(value, label, oracle=False):
    _keys(value, 'root path sha256' + (' locator' if oracle else ''), label)
    if value['root'] not in ('repo', 'workflow') or not isinstance(value['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', value['sha256']):
        _fail('E_EVIDENCE_SCHEMA', f'invalid {label} reference')
    if oracle:
        _string(value['locator'], label + ' locator')
    _relative(value['path'], label)


def _ref(root, value, label, oracle=False, verify=True):
    _ref_shape(value, label, oracle)
    path = _path(root, value['path'], label)
    if verify and _sha(path.read_bytes()) != value['sha256']:
        _fail('E_EVIDENCE_HASH', f'{label} hash mismatch')
    return path


def _git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        _fail('E_EVIDENCE_PATH', f'git {args[0]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def repository(context):
    identity = context.get('identity', {})
    source = Path(_string(identity.get('source_root'), 'identity.source_root'))
    selected = context.get('workspace', {}).get('worktree_path')
    repo = Path(_string(selected, 'worktree_path')) if selected is not None else source
    if not source.is_absolute() or not repo.is_absolute():
        _fail('E_EVIDENCE_PATH', 'repository paths must be absolute')
    for root in (source, repo):
        if not root.is_dir() or root.resolve() != Path(_git(root, 'rev-parse', '--show-toplevel')).resolve():
            _fail('E_EVIDENCE_PATH', 'repository must be an existing Git root')
    if _git(source, 'rev-parse', '--path-format=absolute', '--git-common-dir') != _git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'):
        _fail('E_EVIDENCE_PATH', 'source and worktree have different Git common directories')
    _git(repo, 'rev-parse', '--verify', _string(identity.get('base_commit'), 'base_commit') + '^{commit}')
    return repo.resolve()


def _ids(entries, pattern, label, nonempty=False):
    if not isinstance(entries, list) or (nonempty and not entries):
        _fail('E_AC_SET', f'invalid {label} array')
    ids = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not re.fullmatch(pattern, entry['id']):
            _fail('E_AC_SET', f'invalid {label} id')
        ids.append(entry['id'])
    if len(set(ids)) != len(ids):
        _fail('E_AC_SET', f'duplicate {label} id')
    return set(ids)


def canonical_ac(source):
    lines = source.read_text(encoding='utf-8').splitlines()
    headers = [i for i, line in enumerate(lines) if [x.strip() for x in line.strip().strip('|').split('|')] == ['AC ID', 'Lifecycle', 'Criterion']]
    if len(headers) != 1:
        _fail('E_AC_SET', 'exactly one canonical AC table is required')
    start = headers[0]
    if start + 1 >= len(lines) or not re.fullmatch(r'\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*', lines[start + 1]):
        _fail('E_AC_SET', 'invalid canonical AC table separator')
    active, retired = set(), set()
    for line in lines[start + 2:]:
        if not line.strip().startswith('|'):
            break
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells) < 3 or not re.fullmatch(r'AC[1-9][0-9]*', cells[0]) or cells[1] not in ('ACTIVE', 'RETIRED') or not any(cells[2:]):
            _fail('E_AC_SET', 'invalid canonical AC row')
        aid = cells[0]
        if aid in active | retired:
            _fail('E_AC_SET', 'duplicate canonical AC')
        (active if cells[1] == 'ACTIVE' else retired).add(aid)
    return active, retired


def _known_runner(argv):
    names = {Path(arg).name.lower() for arg in argv}
    return bool(names & {'pytest', 'py.test', 'unittest', 'nosetests', 'jest', 'vitest'}) or (Path(argv[0]).name == 'go' and 'test' in argv) or (Path(argv[0]).name in {'npm', 'pnpm', 'yarn', 'cargo'} and 'test' in argv)


def _check_schema(check, root, repo, retained=False):
    _keys(check, 'id kind argv cwd inputs targets expected_exit assertions', 'check')
    kind = check['kind']
    if kind not in ('pytest', 'go_test', 'command', 'gitlab_ci'):
        _fail('E_EVIDENCE_SCHEMA', 'unsupported check kind')
    if not isinstance(check['argv'], list):
        _fail('E_EVIDENCE_SCHEMA', 'argv must be an array')
    for arg in check['argv']:
        _string(arg, 'argv item')
    if not isinstance(check['inputs'], list) or not check['inputs']:
        _fail('E_EVIDENCE_SCHEMA', 'inputs must be nonempty')
    seen = set()
    for item in check['inputs']:
        if not isinstance(item, dict):
            _fail('E_EVIDENCE_SCHEMA', 'invalid input')
        base = root if item.get('root') == 'workflow' else repo
        _ref_shape(item, 'input')
        path = base / item['path'] if retained else _ref(base, item, 'input', verify=False)
        identity = (item['root'], item['path'])
        if identity in seen:
            _fail('E_EVIDENCE_SCHEMA', 'duplicate input')
        seen.add(identity)
        # Compare actual paths too: a repo reference must not alias control files.
        if path.resolve() in {root / 'context.json', root / 'evidence.json'} or path.resolve().is_relative_to(root / 'evidence'):
            _fail('E_EVIDENCE_PATH', 'control files and execution output cannot be inputs')
    if kind == 'gitlab_ci':
        if check['argv'] != [] or check['cwd'] is not None or check['expected_exit'] is not None or check['assertions'] != []:
            _fail('E_EVIDENCE_SCHEMA', 'invalid CI check')
        _strings(check['targets'], 'CI targets')
        return
    if not check['argv']:
        _fail('E_EVIDENCE_SCHEMA', 'argv must be nonempty')
    _relative(check['cwd'], 'cwd', dot=True)
    if not retained:
        _path(repo, check['cwd'], 'cwd', directory=True)
    _integer(check['expected_exit'], 'expected_exit')
    if kind == 'command':
        if _known_runner(check['argv']) or check['targets'] != [] or not isinstance(check['assertions'], list) or not check['assertions']:
            _fail('E_EVIDENCE_SCHEMA', 'command requires fixed assertions and must not be a known test runner')
        for assertion in check['assertions']:
            _keys(assertion, 'stream op value', 'assertion')
            if assertion['stream'] not in ('stdout', 'stderr') or assertion['op'] not in ('equals', 'contains') or not isinstance(assertion['value'], str) or (assertion['op'] == 'contains' and not assertion['value']):
                _fail('E_EVIDENCE_SCHEMA', 'invalid output assertion')
    else:
        if check['expected_exit'] != 0 or check['assertions'] != []:
            _fail('E_EVIDENCE_SCHEMA', 'test checks require exit 0 and no command assertions')
        if kind == 'pytest':
            _strings(check['targets'], 'pytest targets')
            if any('::' not in item for item in check['targets']):
                _fail('E_EVIDENCE_SCHEMA', 'pytest targets must be exact node IDs')
        else:
            if not isinstance(check['targets'], list) or not check['targets']:
                _fail('E_EVIDENCE_SCHEMA', 'Go targets must be nonempty')
            pairs = []
            for item in check['targets']:
                _keys(item, 'package test', 'Go target')
                pairs.append((_string(item['package'], 'package'), _string(item['test'], 'test')))
            if len(set(pairs)) != len(pairs):
                _fail('E_EVIDENCE_SCHEMA', 'duplicate Go target')
            if Path(check['argv'][0]).name == 'go' and (check['argv'][1:2] != ['test'] or '-json' not in check['argv'] or '-count=1' not in check['argv']):
                _fail('E_EVIDENCE_SCHEMA', 'direct Go checks require go test -json -count=1')


def load_contract(context_path, context=None, *, preparing=False):
    cpath = Path(context_path).absolute()
    root = cpath.parent.resolve()
    context = _json(cpath) if context is None else context
    repo = repository(context)
    recorded_root = context.get('identity', {}).get('artifact_root')
    if recorded_root is not None and Path(recorded_root).resolve() != root:
        _fail('E_EVIDENCE_PATH', 'context artifact_root mismatch')
    return _load_manifest(root, repo, context.get('identity', {}).get('workflow_id'), preparing=preparing)


def _load_manifest(root, repo, workflow_id, retained=False, preparing=False):
    manifest = _json(root / 'evidence.json')
    _keys(manifest, 'version workflow_id source allowlist active retired checks review ci' + (' assurance' if isinstance(manifest, dict) and manifest.get('version') == 2 else ''), 'evidence')
    _integer(manifest['version'], 'version')
    if manifest['version'] not in (1, 2) or _string(manifest['workflow_id'], 'workflow_id') != workflow_id:
        _fail('E_EVIDENCE_SCHEMA', 'workflow identity/version mismatch')
    source = manifest['source']
    if not isinstance(source, dict) or source.get('root') != 'workflow' or source.get('path') not in ('spec.md', 'tasks/01-short-path.md'):
        _fail('E_EVIDENCE_PATH', 'source must be canonical spec or short task')
    source_path = _ref(root, source, 'source')
    _keys(manifest['allowlist'], 'version paths', 'allowlist')
    _integer(manifest['allowlist']['version'], 'allowlist version')
    if manifest['allowlist']['version'] != 1:
        _fail('E_EVIDENCE_SCHEMA', 'invalid allowlist version')
    for path in _strings(manifest['allowlist']['paths'], 'allowlist paths', nonempty=False):
        _relative(path, 'allowlist path')
    active = _ids(manifest['active'], r'AC[1-9][0-9]*', 'active', nonempty=True)
    retired = _ids(manifest['retired'], r'AC[1-9][0-9]*', 'retired')
    if active & retired or (active, retired) != canonical_ac(source_path):
        _fail('E_AC_SET', 'registry differs from canonical AC table')
    checks = _ids(manifest['checks'], r'[a-z][a-z0-9_-]*', 'check', nonempty=True)
    for check in manifest['checks']:
        _check_schema(check, root, repo, retained or preparing)
    referenced = set()
    for entry in manifest['active']:
        _keys(entry, 'id oracle plan task checks', 'active AC')
        linked = _strings(entry['checks'], 'AC checks')
        if not linked <= checks:
            _fail('E_AC_SET', 'unknown AC check')
        referenced |= linked
        for field in ('oracle', 'plan', 'task'):
            value = entry[field]
            base = root if isinstance(value, dict) and value.get('root') == 'workflow' else repo
            _ref(base, value, field, oracle=field == 'oracle')
    for entry in manifest['retired']:
        _keys(entry, 'id reason', 'retired AC')
        _string(entry['reason'], 'retired reason')
    if referenced != checks:
        _fail('E_AC_SET', 'unreferenced checks')
    # Review may be absent or stale while collecting a new execution contract.
    if manifest['review'] is not None:
        _review_schema(manifest)
    _ci_schema(manifest, root, repo)
    if manifest['version'] == 2:
        validate_assurance(manifest['assurance'], manifest['active'], manifest['checks'])
    return manifest


def validate_assurance(value, active, checks):
    """Validate declared risk and check mappings, not their semantic adequacy."""
    _keys(value, 'risk reason existing_contract bounded_blast adequate_oracle protected_boundaries risks important', 'assurance')
    if value['risk'] not in ('low', 'medium', 'high'):
        _fail('E_ASSURANCE', 'unknown risk')
    _string(value['reason'], 'assurance reason')
    for field in ('existing_contract', 'bounded_blast', 'adequate_oracle'):
        if type(value[field]) is not bool:
            _fail('E_ASSURANCE', f'{field} must be boolean')
    boundaries = _strings(value['protected_boundaries'], 'protected boundaries', nonempty=False)
    check_ids = {c['id'] for c in checks}
    linked = {a['id']: set(a['checks']) for a in active}
    for field in ('risks', 'important'):
        if not isinstance(value[field], list):
            _fail('E_ASSURANCE', f'{field} must be an array')
    kinds = set()
    for risk in value['risks']:
        _keys(risk, 'kind checks', 'assurance risk')
        kind = _string(risk['kind'], 'risk kind')
        if kind not in ('concurrency', 'persistence', 'api', 'security', 'integration', 'performance') or kind in kinds:
            _fail('E_ASSURANCE', 'unknown or duplicate risk kind')
        kinds.add(kind)
        if not _strings(risk['checks'], 'risk checks') <= check_ids:
            _fail('E_ASSURANCE', 'unknown risk check')
    ids = set()
    for item in value['important']:
        _keys(item, 'id needs', 'important AC')
        aid = _string(item['id'], 'important id')
        if aid not in linked or aid in ids:
            _fail('E_ASSURANCE', 'unknown or duplicate important AC')
        ids.add(aid)
        if not isinstance(item['needs'], list) or not item['needs']:
            _fail('E_ASSURANCE', 'important needs must be nonempty')
        needs = set()
        for need in item['needs']:
            _keys(need, 'kind checks', 'important need')
            kind = _string(need['kind'], 'need kind')
            if kind not in ('concrete', 'negative', 'invariant', 'reference') or kind in needs:
                _fail('E_ASSURANCE', 'unknown or duplicate need kind')
            needs.add(kind)
            if not _strings(need['checks'], 'need checks') <= linked[aid]:
                _fail('E_ASSURANCE', 'need check not linked to AC')
        if value['risk'] == 'high' and not needs & {'negative', 'invariant', 'reference'}:
            _fail('E_ASSURANCE', 'HIGH important AC needs a nonconcrete oracle')
    if value['risk'] == 'low' and (boundaries or kinds or not all(value[f] for f in ('existing_contract', 'bounded_blast', 'adequate_oracle'))):
        _fail('E_ASSURANCE', 'LOW eligibility not met')
    if (boundaries or kinds & {'api', 'security'} or not value['bounded_blast']) and value['risk'] != 'high':
        _fail('E_ASSURANCE', 'declared boundary requires HIGH')
    if value['risk'] == 'high' and (not boundaries or not ids):
        _fail('E_ASSURANCE', 'HIGH requires boundaries and important ACs')


def assurance_projection(manifest):
    return dict(source=manifest['source'], assurance=manifest['assurance'],
                active=[{k: a[k] for k in ('id', 'oracle', 'checks')} for a in manifest['active']],
                checks=[{k: c[k] for k in ('id', 'kind', 'argv', 'cwd', 'targets', 'expected_exit', 'assertions')} for c in manifest['checks']])


def assurance_contract(manifest):
    return dict(projection_hash='sha256:' + _sha(_canonical(assurance_projection(manifest))))


def validate_assurance_contract(context, manifest, *, complete=False):
    fixed = context.get('execution', {}).get('gates', {}).get('assurance_contract')
    if manifest['version'] == 1:
        if fixed is not None:
            _fail('E_ASSURANCE_FIXED', 'cannot downgrade a frozen v2 contract')
        return
    if fixed != assurance_contract(manifest):
        _fail('E_ASSURANCE_FIXED', 'missing or changed preimplementation assurance contract')
    if complete and not manifest['assurance']['adequate_oracle']:
        _fail('E_ASSURANCE', 'adequate oracle is required for completion')


def _review_schema(manifest):
    review = manifest['review']
    _keys(review, 'path hash reviewed_contract_hash snapshot_id verdict ac', 'review')
    for key in ('path', 'hash', 'reviewed_contract_hash', 'snapshot_id'):
        _string(review[key], 'review ' + key)
    _relative(review['path'], 'review path')
    if not re.fullmatch('[0-9a-f]{64}', review['hash']) or any(not re.fullmatch('sha256:[0-9a-f]{64}', review[key]) for key in ('reviewed_contract_hash', 'snapshot_id')):
        _fail('E_REVIEW', 'invalid review hash')
    if review['verdict'] not in ('APPROVED', 'CHANGES_REQUIRED'):
        _fail('E_REVIEW', 'unknown review verdict')
    if _ids(review['ac'], r'AC[1-9][0-9]*', 'review AC') != {a['id'] for a in manifest['active']}:
        _fail('E_AC_SET', 'review active set mismatch')
    linked = {a['id']: set(a['checks']) for a in manifest['active']}
    for item in review['ac']:
        _keys(item, 'id status reason checks', 'review AC')
        if item['status'] not in ('SATISFIED', 'UNSATISFIED', 'UNVERIFIED') or not isinstance(item['reason'], str):
            _fail('E_REVIEW', 'invalid AC status/reason')
        if _strings(item['checks'], 'review checks') != linked[item['id']]:
            _fail('E_AC_SET', 'review check set mismatch')
        if item['status'] == 'UNVERIFIED':
            _string(item['reason'], 'UNVERIFIED reason')


def validate_review(context_path, manifest, snapshot_id=None):
    """Gate-side review verification; never a prerequisite of run_check."""
    if manifest['review'] is None:
        _fail('E_REVIEW', 'review is required')
    _review_schema(manifest)
    review = manifest['review']
    _ref(Path(context_path).resolve().parent, dict(root='workflow', path=review['path'], sha256=review['hash']), 'review')
    if review['reviewed_contract_hash'] != contract_hash(manifest) or review['verdict'] != 'APPROVED' or any(a['status'] == 'UNSATISFIED' for a in review['ac']):
        _fail('E_REVIEW', 'review does not approve this contract')
    if snapshot_id is not None and review['snapshot_id'] != snapshot_id:
        _fail('E_SNAPSHOT', 'review snapshot mismatch')
    return review


def _ci_schema(manifest, root, repo):
    jobs = {t for c in manifest['checks'] if c['kind'] == 'gitlab_ci' for t in c['targets']}
    ci = manifest['ci']
    if not jobs:
        if ci is not None:
            _fail('E_EVIDENCE_SCHEMA', 'CI config without CI checks')
        return
    _keys(ci, 'host project_id required_jobs delegated_ac authorization_ref', 'CI')
    if not isinstance(ci['host'], str) or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', ci['host']):
        _fail('E_EVIDENCE_SCHEMA', 'CI host must be a hostname')
    _integer(ci['project_id'], 'project_id', 1)
    ci_ids = {c['id'] for c in manifest['checks'] if c['kind'] == 'gitlab_ci'}
    delegated = {a['id'] for a in manifest['active'] if ci_ids & set(a['checks'])}
    if _strings(ci['required_jobs'], 'required_jobs') != jobs or _strings(ci['delegated_ac'], 'delegated_ac') != delegated:
        _fail('E_AC_SET', 'CI delegation set mismatch')
    value = ci['authorization_ref']
    _ref(root if isinstance(value, dict) and value.get('root') == 'workflow' else repo, value, 'authorization', oracle=True)


def _snapshot(repo, context, manifest):
    spec = importlib.util.spec_from_file_location('workflow_review_snapshot', Path(__file__).with_name('review_snapshot.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        result = module.snapshot(repo, context['identity']['base_commit'], manifest['allowlist'], 'worktree')
    except Exception as exc:
        _fail('E_SNAPSHOT', str(exc))
    return dict(snapshot_id=result.review_snapshot_id, manifest=result.manifest, preflight=result.preflight)


def _input_hashes(root, repo, check, expected=True):
    hashes = []
    for value in check['inputs']:
        path = _ref(root if value['root'] == 'workflow' else repo, value, 'input', verify=expected)
        hashes.append(dict(root=value['root'], path=value['path'], sha256=_sha(path.read_bytes())))
    return hashes


@contextlib.contextmanager
def _lock(root):
    fd = os.open(root, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _fail('E_EVIDENCE_BUSY', 'workflow is busy')
        yield
    finally:
        os.close(fd)


def _atomic_new(path, value):
    """Publish a fully flushed JSON file without replacing an existing record."""
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(_canonical(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(temporary)


def pytest_collection_modifyitems(items):
    """Pytest plugin: retain real IDs including parameters, classes and dots."""
    run_id = os.environ.get('WORKFLOW_EVIDENCE_RUN_ID')
    if run_id:
        for item in items:
            item.user_properties.extend([('workflow_nodeid', item.nodeid), ('workflow_run_id', run_id)])


def parse_pytest(raw, targets, run_id):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        _fail('E_CHECK_RESULT', f'invalid JUnit: {exc}')
    observed = []
    for case in root.iter('testcase'):
        properties = {}
        for prop in case.findall('./properties/property'):
            name = prop.get('name')
            if name in ('workflow_nodeid', 'workflow_run_id'):
                if name in properties:
                    _fail('E_CHECK_RESULT', 'duplicate JUnit identity property')
                properties[name] = prop.get('value')
        if properties.get('workflow_run_id') != run_id or not properties.get('workflow_nodeid'):
            _fail('E_CHECK_RESULT', 'JUnit belongs to another run or lacks exact node ID')
        observed.append(properties['workflow_nodeid'])
        if any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped')):
            _fail('E_CHECK_RESULT', 'failed or skipped pytest target')
    if not observed or len(set(observed)) != len(observed) or set(observed) != set(targets):
        _fail('E_CHECK_RESULT', 'expected pytest targets were not observed exactly')
    return observed


def parse_go(raw, targets):
    events = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        event = _decode(line)
        if not isinstance(event, dict) or set(event) - {'Time', 'Action', 'Package', 'Test', 'Elapsed', 'Output', 'FailedBuild'} or not isinstance(event.get('Action'), str) or not isinstance(event.get('Package'), str):
            _fail('E_CHECK_RESULT', 'invalid Go event')
        if any(not isinstance(event[key], str) for key in ('Time', 'Test', 'Output', 'FailedBuild') if key in event) or ('Elapsed' in event and (type(event['Elapsed']) not in (int, float) or not math.isfinite(event['Elapsed']))):
            _fail('E_CHECK_RESULT', 'invalid Go event field type')
        if event['Action'] not in ('start', 'run', 'pause', 'cont', 'pass', 'bench', 'fail', 'output', 'skip'):
            _fail('E_CHECK_RESULT', 'unknown Go action')
        if event['Action'] in ('fail', 'skip') or '(cached)' in str(event.get('Output', '')):
            _fail('E_CHECK_RESULT', 'Go failure, skip or cached execution')
        events.append(event)
    if not events:
        _fail('E_CHECK_RESULT', 'empty Go output')
    observed = []
    for target in targets:
        package, test = target['package'], target['test']
        actions = [e['Action'] for e in events if e.get('Package') == package and e.get('Test') == test]
        if actions.count('run') != 1 or actions.count('pass') != 1 or actions.index('run') > actions.index('pass'):
            _fail('E_CHECK_RESULT', f'Go target was not executed and passed: {package}::{test}')
        package_passes = [i for i, e in enumerate(events) if e.get('Package') == package and 'Test' not in e and e['Action'] == 'pass']
        target_pass = next(i for i, e in enumerate(events) if e.get('Package') == package and e.get('Test') == test and e['Action'] == 'pass')
        if len(package_passes) != 1 or package_passes[0] < target_pass:
            _fail('E_CHECK_RESULT', f'Go package did not pass: {package}')
        observed.append(f'{package}::{test}')
    return observed


def _adapter(check, repo, run_dir, run_id):
    env = os.environ.copy()
    settings = {}
    if check['kind'] == 'pytest':
        try:
            existing = shlex.split(env.get('PYTEST_ADDOPTS', ''))
        except ValueError as exc:
            _fail('E_EVIDENCE_SCHEMA', f'invalid PYTEST_ADDOPTS: {exc}')
        if env.get('WORKFLOW_EVIDENCE_RUN_ID'):
            # Nested collectors replace only options injected by their parent.
            inherited = []
            i = 0
            while i < len(existing):
                arg = existing[i]
                if arg.startswith(('--junitxml=', '--rootdir=')):
                    i += 1
                elif existing[i:i + 2] == ['-p', 'workflow_evidence']:
                    i += 2
                else:
                    inherited.append(arg)
                    i += 1
            existing = inherited
        if any(arg.startswith(('--junit', '--rootdir', '-p')) for arg in check['argv'] + existing):
            _fail('E_EVIDENCE_SCHEMA', 'reserved pytest JUnit/rootdir/plugin option')
        settings = dict(PYTEST_ADDOPTS=shlex.join(existing + [f'--junitxml={run_dir / "junit.xml"}', f'--rootdir={repo}', '-p', 'workflow_evidence']), WORKFLOW_EVIDENCE_RUN_ID=run_id, PYTHONDONTWRITEBYTECODE='1')
        env.update(settings)
        helper = str(Path(__file__).resolve().parent)
        env['PYTHONPATH'] = helper + os.pathsep + env.get('PYTHONPATH', '')
        settings['pythonpath_prepend'] = helper
    return env, settings


def _result(check, rc, stdout, stderr, report, run_id):
    reasons, observed = [], []
    if rc != check['expected_exit']:
        reasons.append(f'exit code {rc}, expected {check["expected_exit"]}')
    try:
        if check['kind'] == 'pytest':
            if report is None:
                _fail('E_CHECK_RESULT', 'JUnit report missing')
            observed = parse_pytest(report, check['targets'], run_id)
        elif check['kind'] == 'go_test':
            observed = parse_go(stdout, check['targets'])
        else:
            for assertion in check['assertions']:
                stream = stdout if assertion['stream'] == 'stdout' else stderr
                good = stream == assertion['value'] if assertion['op'] == 'equals' else assertion['value'] in stream
                if not good:
                    reasons.append(f'{assertion["stream"]} {assertion["op"]} assertion failed')
    except EvidenceError as exc:
        reasons.append(str(exc))
    return dict(check_id=check['id'], status='failed' if reasons else 'passed', reasons=reasons, observed_targets=observed)


START_KEYS = 'version run_id sequence workflow_id contract_hash check_ids kind argv cwd started_at commit snapshot_before inputs_before ci'
RECEIPT_KEYS = START_KEYS + ' finished_at exit_code snapshot_after inputs_after files results'


def _snapshot_schema(value):
    _keys(value, 'snapshot_id manifest preflight', 'snapshot')
    _keys(value['manifest'], 'base_commit paths', 'snapshot manifest')
    _string(value['manifest']['base_commit'], 'snapshot base_commit')
    if not isinstance(value['manifest']['paths'], list):
        _fail('E_SNAPSHOT', 'invalid snapshot paths')
    paths = []
    for entry in value['manifest']['paths']:
        _keys(entry, 'content_sha256 mode path state', 'snapshot entry')
        paths.append(_relative(entry['path'], 'snapshot path'))
        if entry['state'] not in ('present', 'deleted', 'absent') or entry['mode'] not in ('100644', '100755', '120000', None) or (entry['content_sha256'] is not None and (not isinstance(entry['content_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['content_sha256']))):
            _fail('E_SNAPSHOT', 'invalid snapshot entry')
    if len(set(paths)) != len(paths):
        _fail('E_SNAPSHOT', 'duplicate snapshot paths')
    _keys(value['preflight'], 'external_dirty_paths external_staged_paths shipping_blocked', 'preflight')
    for key in ('external_dirty_paths', 'external_staged_paths'):
        _strings(value['preflight'][key], key, nonempty=False)
    if type(value['preflight']['shipping_blocked']) is not bool:
        _fail('E_SNAPSHOT', 'invalid preflight flag')
    if value['snapshot_id'] != 'sha256:' + _sha(_canonical(value['manifest'])):
        _fail('E_SNAPSHOT', 'invalid snapshot record')


def _start_schema(start, directory):
    _keys(start, START_KEYS, 'start')
    _integer(start['version'], 'start version')
    _integer(start['sequence'], 'sequence', 1)
    if start['version'] != 1 or start['run_id'] != directory.name:
        _fail('E_ATTEMPT', 'invalid run identity')
    try:
        if str(uuid.UUID(start['run_id'])) != start['run_id']:
            raise ValueError('not canonical UUID')
    except (ValueError, TypeError, AttributeError):
        _fail('E_ATTEMPT', 'invalid run UUID')
    for field in ('workflow_id', 'contract_hash', 'kind', 'commit'):
        _string(start[field], field)
    if type(start['started_at']) not in (int, float) or not math.isfinite(start['started_at']):
        _fail('E_ATTEMPT', 'invalid start timestamp')
    _strings(start['check_ids'], 'start checks')
    if not isinstance(start['argv'], list) or not all(isinstance(a, str) for a in start['argv']) or not isinstance(start['inputs_before'], list):
        _fail('E_ATTEMPT', 'invalid start command/inputs')
    for value in start['inputs_before']:
        _ref_shape(value, 'start input')
    if start['kind'] == 'gitlab_ci':
        _keys(start['ci'], 'host project_id pipeline_id', 'CI start')
        _integer(start['ci']['project_id'], 'project_id', 1)
        _integer(start['ci']['pipeline_id'], 'pipeline_id', 1)
        _string(start['ci']['host'], 'host')
        if start['argv'] != [] or start['cwd'] is not None:
            _fail('E_ATTEMPT', 'invalid CI start command')
    elif start['ci'] is not None or not start['argv'] or not isinstance(start['cwd'], str):
        _fail('E_ATTEMPT', 'invalid local start')
    _snapshot_schema(start['snapshot_before'])


def _starts(root):
    runs = root / 'evidence' / 'runs'
    if (root / 'evidence').exists() or (root / 'evidence').is_symlink():
        _path(root, 'evidence', 'evidence directory', directory=True)
    if not runs.exists():
        return []
    _path(root, 'evidence/runs', 'runs', directory=True)
    result, sequences = [], set()
    for directory in sorted(runs.iterdir()):
        if directory.is_symlink() or not directory.is_dir():
            _fail('E_ATTEMPT', 'invalid run directory')
        path = directory / 'start.json'
        # A directory can exist briefly before atomic start publication, under lock.
        if not path.exists():
            _fail('E_ATTEMPT', 'run directory has no start record')
        start = _json(path)
        _start_schema(start, directory)
        if start['sequence'] in sequences:
            _fail('E_ATTEMPT', 'duplicate sequence')
        sequences.add(start['sequence'])
        result.append((directory, start))
    return result


def latest_start(context_path, manifest, check_id, snapshot_id):
    """Select starts before looking at receipts; missing/latest failures block."""
    matches = [(directory, start) for directory, start in _starts(Path(context_path).resolve().parent) if start['workflow_id'] == manifest['workflow_id'] and start['contract_hash'] == contract_hash(manifest) and check_id in start['check_ids'] and start['snapshot_before']['snapshot_id'] == snapshot_id]
    if not matches:
        _fail('E_ATTEMPT', f'no attempt for {check_id} at this contract/snapshot')
    return max(matches, key=lambda item: item[1]['sequence'])


def run_check(context_path, check_id):
    cpath = Path(context_path).absolute()
    root = cpath.parent.resolve()
    with _lock(root):
        context = _json(cpath)
        manifest = load_contract(cpath, context)
        validate_assurance_contract(context, manifest)
        repo = repository(context)
        check = next((c for c in manifest['checks'] if c['id'] == check_id), None)
        if check is None or check['kind'] == 'gitlab_ci':
            _fail('E_CHECK_RESULT', 'unknown or nonlocal check')
        return run_local_check(root, repo, context, manifest, check)


def run_local_check(root, repo, context, manifest, check):
    """Collect one local execution under the caller's workflow/record lock."""
    check_id = check['id']
    starts = _starts(root)
    before = _snapshot(repo, context, manifest)
    inputs = _input_hashes(root, repo, check)
    run_id = str(uuid.uuid4())
    run_dir = root / 'evidence' / 'runs' / run_id
    env, settings = _adapter(check, repo, run_dir, run_id)
    run_dir.mkdir(parents=True)
    start = dict(version=1, run_id=run_id, sequence=max((s['sequence'] for _, s in starts), default=0) + 1, workflow_id=manifest['workflow_id'], contract_hash=contract_hash(manifest), check_ids=[check_id], kind=check['kind'], argv=check['argv'], cwd=check['cwd'], started_at=time.time(), commit=_git(repo, 'rev-parse', 'HEAD'), snapshot_before=before, inputs_before=inputs, ci=None)
    _atomic_new(run_dir / 'start.json', start)
    # Interruption deliberately leaves the latest start without a receipt.
    proc = subprocess.run(check['argv'], cwd=_path(repo, check['cwd'], 'cwd', directory=True), env=env, capture_output=True, shell=False, check=False)
    (run_dir / 'stdout.log').write_bytes(proc.stdout)
    (run_dir / 'stderr.log').write_bytes(proc.stderr)
    report_path = run_dir / 'junit.xml'
    report = report_path.read_bytes() if report_path.is_file() and not report_path.is_symlink() else None
    try:
        result = _result(check, proc.returncode, proc.stdout.decode('utf-8', 'strict'), proc.stderr.decode('utf-8', 'strict'), report, run_id)
    except UnicodeError:
        result = dict(check_id=check_id, status='failed', reasons=['output is not UTF-8'], observed_targets=[])
    after = _snapshot(repo, context, manifest)
    inputs_after = _input_hashes(root, repo, check, expected=False)
    if before['snapshot_id'] != after['snapshot_id'] or inputs != inputs_after:
        result['status'] = 'failed'
        result['reasons'].append('snapshot or declared inputs changed during execution')
    _atomic_new(run_dir / 'inputs.json', dict(expected=check['inputs'], before=inputs, after=inputs_after))
    _atomic_new(run_dir / 'adapter.json', settings)
    files = []
    for path in sorted(run_dir.iterdir()):
        if path.name != 'start.json':
            if path.is_symlink() or not path.is_file():
                _fail('E_EVIDENCE_PATH', 'runner produced a nonregular output')
            files.append(dict(root='workflow', path=path.relative_to(root).as_posix(), sha256=_sha(path.read_bytes())))
    receipt = dict(start, finished_at=time.time(), exit_code=proc.returncode, snapshot_after=after, inputs_after=inputs_after, files=files, results=[result])
    _atomic_new(run_dir / 'receipt.json', receipt)
    return receipt


def validate_receipt(root, manifest, check, directory, start, require_pass=True):
    """Verify immutable receipt/raw/input-manifest consistency without live Git.

    Export/cleanup may reuse this primitive with relocated workflow references.
    It does not assert that current source files or a review are still valid.
    """
    receipt = _json(directory / 'receipt.json')
    _keys(receipt, RECEIPT_KEYS, 'receipt')
    _start_schema({key: receipt[key] for key in START_KEYS.split()}, directory)
    if {key: receipt[key] for key in START_KEYS.split()} != start:
        _fail('E_ATTEMPT', 'receipt does not match start')
    if start['contract_hash'] != contract_hash(manifest) or start['workflow_id'] != manifest['workflow_id'] or start['check_ids'] != [check['id']] or any(start[key] != check[key] for key in ('kind', 'argv', 'cwd')):
        _fail('E_ATTEMPT', 'receipt contract/check mismatch')
    _integer(receipt['exit_code'], 'exit_code')
    if type(receipt['finished_at']) not in (int, float) or not math.isfinite(receipt['finished_at']) or receipt['finished_at'] < start['started_at']:
        _fail('E_ATTEMPT', 'invalid finish timestamp')
    _snapshot_schema(receipt['snapshot_after'])
    if not isinstance(receipt['inputs_after'], list):
        _fail('E_ATTEMPT', 'invalid inputs after execution')
    for value in receipt['inputs_after']:
        _ref_shape(value, 'input after execution')
    if start['inputs_before'] != check['inputs']:
        _fail('E_ATTEMPT', 'start inputs differ from contract')
    changed = receipt['snapshot_after']['snapshot_id'] != start['snapshot_before']['snapshot_id'] or receipt['inputs_after'] != start['inputs_before']
    if require_pass and changed:
        _fail('E_ATTEMPT', 'snapshot/inputs changed')
    if not isinstance(receipt['files'], list):
        _fail('E_ATTEMPT', 'invalid files')
    files = {}
    for value in receipt['files']:
        path = _ref(root, value, 'raw file')
        if value['root'] != 'workflow' or path.parent != directory or path.name in files or path.name in ('start.json', 'receipt.json'):
            _fail('E_ATTEMPT', 'invalid raw file location')
        files[path.name] = path
    if check['kind'] == 'gitlab_ci':
        return _validate_ci_raw(root, manifest, check, directory, start, receipt, files, require_pass, changed)
    required = {'stdout.log', 'stderr.log', 'inputs.json', 'adapter.json'} | ({'junit.xml'} if check['kind'] == 'pytest' else set())
    if not required <= files.keys():
        _fail('E_ATTEMPT', 'missing raw evidence')
    adapter = _json(files['adapter.json'])
    _keys(adapter, 'PYTEST_ADDOPTS WORKFLOW_EVIDENCE_RUN_ID PYTHONDONTWRITEBYTECODE pythonpath_prepend' if check['kind'] == 'pytest' else '', 'adapter settings')
    for key, value in adapter.items():
        _string(value, 'adapter ' + key)
    if check['kind'] == 'pytest' and adapter['WORKFLOW_EVIDENCE_RUN_ID'] != start['run_id']:
        _fail('E_ATTEMPT', 'adapter run identity mismatch')
    if _json(files['inputs.json']) != dict(expected=check['inputs'], before=start['inputs_before'], after=receipt['inputs_after']):
        _fail('E_ATTEMPT', 'input manifest mismatch')
    try:
        result = _result(check, receipt['exit_code'], files['stdout.log'].read_bytes().decode('utf-8'), files['stderr.log'].read_bytes().decode('utf-8'), files['junit.xml'].read_bytes() if 'junit.xml' in files else None, start['run_id'])
    except UnicodeError:
        _fail('E_CHECK_RESULT', 'invalid output encoding')
    if changed:
        result['status'] = 'failed'
        result['reasons'].append('snapshot or declared inputs changed during execution')
    if receipt['results'] != [result] or (require_pass and result['status'] != 'passed'):
        _fail('E_CHECK_RESULT', 'latest attempt did not pass measured assertions')
    return receipt


def validate_latest_receipt(context_path, manifest, check_id, snapshot=None):
    """Validate latest local receipt, including current snapshot and inputs.

    Caller must hold the workflow directory lock when coordinating a mutation.
    """
    cpath = Path(context_path).absolute()
    context = _json(cpath)
    current = load_contract(cpath, context)
    validate_assurance_contract(context, current)
    if contract_hash(current) != contract_hash(manifest):
        _fail('E_EVIDENCE_HASH', 'supplied contract is stale')
    repo = repository(context)
    check = next((c for c in manifest['checks'] if c['id'] == check_id), None)
    if check is None or check['kind'] == 'gitlab_ci':
        _fail('E_CHECK_RESULT', 'not a local check')
    live = _snapshot(repo, context, manifest) if snapshot is None else snapshot
    directory, start = latest_start(cpath, manifest, check_id, live['snapshot_id'])
    receipt = validate_receipt(cpath.parent.resolve(), manifest, check, directory, start)
    if _input_hashes(cpath.parent.resolve(), repo, check) != receipt['inputs_after']:
        _fail('E_EVIDENCE_HASH', 'live inputs differ from receipt')
    return receipt


# Phase names denote work beginning; only completed checkpoints are cumulative.
_REVIEW_PHASES = frozenset(('LOCAL_VERIFICATION', 'LOCAL_COMPLETE', 'COMMIT',
                           'PUSH_MR', 'CI', 'MR_READY', 'MERGE_CHECK', 'WT_REMOVE', 'ARTIFACT_REMOVE'))
_SHIPPING_PHASES = _REVIEW_PHASES - {'LOCAL_VERIFICATION', 'LOCAL_COMPLETE'}
_COMMITTED_PHASES = _SHIPPING_PHASES - {'COMMIT'}
_CI_COMPLETE_PHASES = frozenset(('MR_READY', 'MERGE_CHECK', 'WT_REMOVE', 'ARTIFACT_REMOVE'))
_CLEANUP_PHASES = frozenset(('WT_REMOVE', 'ARTIFACT_REMOVE'))



def _gate_snapshot(repo, context, manifest, source):
    spec = importlib.util.spec_from_file_location('workflow_gate_snapshot', Path(__file__).with_name('review_snapshot.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        if source == 'commit':
            result = module.snapshot_from_commit(repo, context['identity']['base_commit'], manifest['allowlist'], context['shipping']['commit'])
        else:
            result = module.snapshot(repo, context['identity']['base_commit'], manifest['allowlist'], source)
    except module.SnapshotError as exc:
        _fail('E_SNAPSHOT', str(exc))
    return dict(snapshot_id=result.review_snapshot_id, manifest=result.manifest, preflight=result.preflight)


def evaluate_gates(context_path, current, candidate, *, normative=False):
    """Return measured execution fields, or raise before the caller commits.

    This function does not lock or write; durable mutation/check-gates already
    hold the workflow directory lock. Caller-provided gate strings are ignored.
    """
    target = candidate['state']['phase']
    old_fixed = current['execution']['gates'].get('assurance_contract')
    new_fixed = candidate['execution']['gates'].get('assurance_contract')
    if old_fixed != new_fixed and not (normative and new_fixed is None):
        _fail('E_ASSURANCE_FIXED', 'caller cannot overwrite assurance contract')
    if target == 'TASKS':
        cp = Path(context_path).absolute()
        if (cp.parent / 'evidence.json').exists():
            recorded = _json(cp.parent / 'evidence.json')
            # Legacy TASKS entry did not require a complete execution manifest.
            if old_fixed is not None or (isinstance(recorded, dict) and recorded.get('version') == 2):
                manifest = load_contract(cp, candidate, preparing=True)
                if manifest['version'] == 2 and old_fixed is None:
                    if current['state']['phase'] != 'WORKTREE_READY':
                        _fail('E_ASSURANCE_FIXED', 'initial freeze requires first TASKS entry')
                    return dict(gates=dict(assurance_contract=assurance_contract(manifest)))
                validate_assurance_contract(candidate, manifest)
        elif old_fixed is not None:
            _fail('E_ASSURANCE_FIXED', 'frozen manifest is missing')
    # Recovery and an explicit stop remain possible even for legacy evidence.
    if target in ('USER_DECISION_REQUIRED', 'TASKS', 'DEBUGGING', 'SPEC_REVIEWS'):
        return {}
    previous = current['state']['phase']
    if previous == 'USER_DECISION_REQUIRED':
        previous = current['state']['stopped_from']
    phases = {previous, target}
    if not phases & _REVIEW_PHASES:
        if target == 'FINAL_REVIEW':
            cp = Path(context_path).absolute()
            if (cp.parent / 'evidence.json').exists():
                recorded = _json(cp.parent / 'evidence.json')
                if old_fixed is not None or (isinstance(recorded, dict) and recorded.get('version') == 2):
                    validate_assurance_contract(candidate, load_contract(cp, candidate))
            elif old_fixed is not None:
                _fail('E_ASSURANCE_FIXED', 'frozen manifest is missing')
        return {}
    cleanup = bool(phases & _CLEANUP_PHASES)
    cp = Path(context_path).absolute()
    if cleanup:
        retained = resolve_cleanup_evidence(cp, candidate)
        manifest = retained['manifest']
        root, repo = Path(retained['workflow_root']), Path(retained['repo_root'])
        # Only Git object reads use source_root in cleanup mode.
        object_repo = Path(candidate['identity']['source_root'])
    else:
        manifest = load_contract(cp, candidate)
        root, repo = cp.parent.resolve(), repository(candidate)
        object_repo = repo
    validate_assurance_contract(candidate, manifest, complete=True)
    committed = bool(phases & _COMMITTED_PHASES) or (previous == 'COMMIT' and candidate['shipping']['commit'] is not None)
    snap = _gate_snapshot(object_repo, candidate, manifest, 'commit') if committed else _snapshot(repo, candidate, manifest)
    review = validate_review(root / 'context.json', manifest, snap['snapshot_id'])
    records = dict(final_review=dict(status='passed', contract_hash=contract_hash(manifest),
                                    snapshot_id=snap['snapshot_id'], review_hash=review['hash']),
                   local_verification=None)
    need_local = bool(phases & (_SHIPPING_PHASES | {'LOCAL_COMPLETE'}))
    require_ci = bool(phases & _CI_COMPLETE_PHASES) or 'LOCAL_COMPLETE' in phases
    receipts = []
    if need_local:
        for check in manifest['checks']:
            if check['kind'] == 'gitlab_ci' and not require_ci:
                continue  # load_contract already verified the explicit delegation.
            directory, start = latest_start(cp, manifest, check['id'], snap['snapshot_id'])
            if cleanup:
                retained_dir = root / 'evidence' / 'runs' / start['run_id']
                if _json(retained_dir / 'start.json') != start:
                    _fail('E_ATTEMPT', 'cleanup retained attempt differs from latest start')
                directory = retained_dir
            if check['kind'] == 'gitlab_ci':
                receipt = validate_ci_receipt(root, manifest, check, directory, start, candidate['shipping']['commit'])
            else:
                receipt = validate_receipt(root, manifest, check, directory, start)
            if not cleanup and _input_hashes(root, repo, check) != receipt['inputs_after']:
                _fail('E_EVIDENCE_HASH', 'live inputs differ from receipt')
            receipts.append(receipt['run_id'])
        if phases & _CI_COMPLETE_PHASES and not any(c['kind'] == 'gitlab_ci' for c in manifest['checks']):
            _fail('E_CI', 'target commit has no required CI evidence')
        records['local_verification'] = dict(status='passed', contract_hash=contract_hash(manifest),
                                             snapshot_id=snap['snapshot_id'], run_ids=receipts,
                                             ci_pending=bool(manifest['ci']) and not require_ci)
    if need_local:
        validate_human_review(cp, candidate, manifest=manifest, snap=snap, retained=retained if cleanup else None)
    if phases & _SHIPPING_PHASES:
        if candidate['authorization']['shipping_authorized'] is not True:
            _fail('E_AUTHORIZATION', 'shipping authorization is required')
        # An existing COMMIT phase also represents an unfinished precommit
        # checkpoint. Once a commit is required, consult only its fixed tree.
        if not committed:
            indexed = _gate_snapshot(repo, candidate, manifest, 'index')
            if indexed['snapshot_id'] != snap['snapshot_id'] or snap['preflight']['shipping_blocked'] or indexed['preflight']['shipping_blocked']:
                _fail('E_SNAPSHOT', 'worktree/index mismatch or external dirty/staged paths')
    return dict(gates=records, review_snapshot_id=snap['snapshot_id'])


def _ci_argv(ci, pipeline_id):
    base = ['glab', 'api', '--hostname', ci['host'], '--method', 'GET']
    endpoint = f"projects/{ci['project_id']}/pipelines/{pipeline_id}"
    return [base + [endpoint], base + ['--paginate', '--output', 'json', endpoint + '/jobs?include_retried=true&per_page=100']]


def _ci_result(manifest, check, start, calls, pipeline_raw, jobs_raw):
    reasons, observed = [], []
    try:
        if any(call['exit_code'] != 0 for call in calls):
            _fail('E_CI', 'GitLab API request failed')
        pipeline, jobs = _decode(pipeline_raw), _decode(jobs_raw)
        identity = dict(id=start['ci']['pipeline_id'], project_id=manifest['ci']['project_id'], sha=start['commit'])
        def matches(value):
            return isinstance(value, dict) and all(type(value.get(k)) is type(v) and value[k] == v for k, v in identity.items())
        if not matches(pipeline) or pipeline.get('status') != 'success':
            _fail('E_CI', 'pipeline identity/status mismatch')
        if not isinstance(jobs, list):
            _fail('E_CI', 'paginated jobs must be one JSON array')
        latest, ids = {}, set()
        for job in jobs:
            if not isinstance(job, dict):
                _fail('E_CI', 'invalid job')
            _integer(job.get('id'), 'job id', 1)
            _string(job.get('name'), 'job name')
            _string(job.get('status'), 'job status')
            if job['id'] in ids or not matches(job.get('pipeline')):
                _fail('E_CI', 'job pipeline identity or duplicate ID mismatch')
            ids.add(job['id'])
            if 'commit' in job and (not isinstance(job['commit'], dict) or job['commit'].get('id') != start['commit']):
                _fail('E_CI', 'job commit mismatch')
            if job['id'] > latest.get(job['name'], {}).get('id', 0):
                latest[job['name']] = job
        for name in manifest['ci']['required_jobs']:
            if name not in latest or latest[name]['status'] != 'success':
                _fail('E_CI', 'required latest job did not succeed: ' + name)
        observed = [dict(name=name, id=latest[name]['id'], status='success') for name in check['targets']]
    except EvidenceError as exc:
        reasons.append(str(exc))
    return dict(check_id=check['id'], status='failed' if reasons else 'passed', reasons=reasons, observed_targets=observed)


def collect_ci(context_path, pipeline_id):
    """Collect the fixed GitLab project using only read-only glab subprocesses."""
    _integer(pipeline_id, 'pipeline_id', 1)
    cp = Path(context_path).absolute()
    root = cp.parent.resolve()
    with _lock(root):
        context = _json(cp)
        manifest = load_contract(cp, context)
        validate_assurance_contract(context, manifest)
        repo = repository(context)
        checks = [c for c in manifest['checks'] if c['kind'] == 'gitlab_ci']
        if not checks:
            _fail('E_CI', 'no fixed CI checks')
        commit = context.get('shipping', {}).get('commit')
        if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40,64}', commit):
            _fail('E_CI', 'shipping commit is required')
        before = _gate_snapshot(repo, context, manifest, 'commit')
        starts = _starts(root)
        # One collection produces one start per fixed check before any API call.
        pending = []
        sequence = max((s['sequence'] for _, s in starts), default=0)
        for check in checks:
            sequence += 1
            run_id = str(uuid.uuid4())
            directory = root / 'evidence' / 'runs' / run_id
            inputs = _input_hashes(root, repo, check)
            directory.mkdir(parents=True)
            start = dict(version=1, run_id=run_id, sequence=sequence, workflow_id=manifest['workflow_id'], contract_hash=contract_hash(manifest), check_ids=[check['id']], kind=check['kind'], argv=[], cwd=None, started_at=time.time(), commit=commit, snapshot_before=before, inputs_before=inputs, ci=dict(host=manifest['ci']['host'], project_id=manifest['ci']['project_id'], pipeline_id=pipeline_id))
            _atomic_new(directory / 'start.json', start)
            pending.append((check, directory, start))
        env = os.environ.copy()
        env.pop('GLAB_DEBUG_HTTP', None)
        calls, raw = [], []
        for name, argv in zip(('pipeline', 'jobs'), _ci_argv(manifest['ci'], pipeline_id)):
            try:
                proc = subprocess.run(argv, cwd=repo, env=env, capture_output=True, shell=False, check=False)
                rc, stdout = proc.returncode, proc.stdout
            except OSError:
                rc, stdout = 127, b''
            calls.append(dict(argv=argv, exit_code=rc, stdout=name + '.json', stderr=name + '.stderr.log'))
            raw.append(stdout)
        after = _gate_snapshot(repo, context, manifest, 'commit')
        receipts = []
        for check, directory, start in pending:
            inputs_after = _input_hashes(root, repo, check, expected=False)
            for call, data in zip(calls, raw):
                (directory / call['stdout']).write_bytes(data)
                (directory / call['stderr']).write_text('GitLab API request failed\n' if call['exit_code'] else '')
            _atomic_new(directory / 'api.json', dict(calls=calls))
            _atomic_new(directory / 'inputs.json', dict(expected=check['inputs'], before=start['inputs_before'], after=inputs_after))
            result = _ci_result(manifest, check, start, calls, *raw)
            if before['snapshot_id'] != after['snapshot_id'] or start['inputs_before'] != inputs_after:
                result['status'] = 'failed'
                result['reasons'].append('snapshot or declared inputs changed during execution')
            files = [dict(root='workflow', path=p.relative_to(root).as_posix(), sha256=_sha(p.read_bytes())) for p in sorted(directory.iterdir()) if p.name != 'start.json']
            receipt = dict(start, finished_at=time.time(), exit_code=next((c['exit_code'] for c in calls if c['exit_code']), 0), snapshot_after=after, inputs_after=inputs_after, files=files, results=[result])
            _atomic_new(directory / 'receipt.json', receipt)
            receipts.append(receipt)
        return receipts


def _validate_ci_raw(root, manifest, check, directory, start, receipt, files, require_pass, changed):
    ci = manifest['ci']
    if start['ci'] != dict(host=ci['host'], project_id=ci['project_id'], pipeline_id=start['ci']['pipeline_id']):
        _fail('E_CI', 'CI start differs from fixed host/project')
    required = {'pipeline.json', 'jobs.json', 'pipeline.stderr.log', 'jobs.stderr.log', 'api.json', 'inputs.json'}
    if set(files) != required:
        _fail('E_CI', 'missing or unexpected CI raw evidence')
    api = _json(files['api.json'])
    _keys(api, 'calls', 'API record')
    if not isinstance(api['calls'], list) or len(api['calls']) != 2:
        _fail('E_CI', 'incomplete API calls')
    for call, name, argv in zip(api['calls'], ('pipeline', 'jobs'), _ci_argv(ci, start['ci']['pipeline_id'])):
        _keys(call, 'argv exit_code stdout stderr', 'API call')
        _integer(call['exit_code'], 'API exit_code')
        if call['argv'] != argv or call['stdout'] != name + '.json' or call['stderr'] != name + '.stderr.log':
            _fail('E_CI', 'API command/raw association mismatch')
        if files[call['stderr']].read_bytes() != (b'GitLab API request failed\n' if call['exit_code'] else b''):
            _fail('E_CI', 'invalid sanitized API diagnostic')
    if receipt['exit_code'] != next((c['exit_code'] for c in api['calls'] if c['exit_code']), 0):
        _fail('E_CI', 'API exit code mismatch')
    if _json(files['inputs.json']) != dict(expected=check['inputs'], before=start['inputs_before'], after=receipt['inputs_after']):
        _fail('E_ATTEMPT', 'input manifest mismatch')
    result = _ci_result(manifest, check, start, api['calls'], files['pipeline.json'].read_bytes(), files['jobs.json'].read_bytes())
    if changed:
        result['status'] = 'failed'
        result['reasons'].append('snapshot or declared inputs changed during execution')
    if receipt['results'] != [result] or (require_pass and result['status'] != 'passed'):
        _fail('E_CI', 'latest CI attempt did not pass measured API results')
    return receipt


def validate_ci_receipt(root, manifest, check, directory, start, commit):
    if start['commit'] != commit:
        _fail('E_CI', 'CI receipt commit differs from shipping commit')
    return validate_receipt(root, manifest, check, directory, start)


def _human_module():
    spec = importlib.util.spec_from_file_location('workflow_human_review', Path(__file__).with_name('human_review.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _file_ref(root, path):
    return dict(root='workflow', path=path.relative_to(root).as_posix(), sha256=_sha(path.read_bytes()))


def _ci_history(root, manifest, snapshot_id):
    """Fingerprint failed and superseded unfinished attempts, never successes."""
    starts = _starts(root)
    history, pending = [], False
    for check in sorted(manifest['checks'], key=lambda c: c['id']):
        if check['kind'] != 'gitlab_ci':
            continue
        matches = sorted(((d, s) for d, s in starts if s['workflow_id'] == manifest['workflow_id']
                          and s['contract_hash'] == contract_hash(manifest)
                          and s['check_ids'] == [check['id']]
                          and s['snapshot_before']['snapshot_id'] == snapshot_id), key=lambda item: item[1]['sequence'])
        if not matches:
            pending = True
        for index, (directory, start) in enumerate(matches):
            receipt_path = directory / 'receipt.json'
            if receipt_path.exists() or receipt_path.is_symlink():
                receipt = validate_receipt(root, manifest, check, directory, start, require_pass=False)
                if receipt['results'][0]['status'] == 'failed':
                    history.append(dict(check_id=check['id'], start=_file_ref(root, directory / 'start.json'),
                                        receipt=_file_ref(root, receipt_path), successor_start=None))
                    if index == len(matches) - 1:
                        _fail('E_CI', 'latest CI attempt failed; repair/retry before human presentation')
            elif index + 1 < len(matches):
                history.append(dict(check_id=check['id'], start=_file_ref(root, directory / 'start.json'), receipt=None,
                                    successor_start=_file_ref(root, matches[index + 1][0] / 'start.json')))
            else:
                pending = True
    return history, pending


def _validate_retained_ci_history(root, manifest, snapshot_id, history):
    """Verify the record's expected history without treating successor-only
    copies as abandoned attempts, and without consulting the original roots.
    """
    starts = _starts(root)
    checks = {c['id']: c for c in manifest['checks'] if c['kind'] == 'gitlab_ci'}
    observed = []
    def selected(value, check):
        path = _ref(root, value, 'retained CI history')
        if value['root'] != 'workflow' or path.name != 'start.json' or path.parent.parent != root / 'evidence' / 'runs':
            _fail('E_ATTEMPT', 'history start has invalid location')
        start = _json(path)
        _start_schema(start, path.parent)
        if start['workflow_id'] != manifest['workflow_id'] or start['contract_hash'] != contract_hash(manifest) or start['check_ids'] != [check['id']] or start['kind'] != 'gitlab_ci' or start['snapshot_before']['snapshot_id'] != snapshot_id:
            _fail('E_ATTEMPT', 'history start check/contract/snapshot mismatch')
        return path.parent, start
    for row in history:
        check = checks.get(row['check_id'])
        if check is None:
            _fail('E_ATTEMPT', 'unknown history CI check')
        directory, start = selected(row['start'], check)
        observed.append((check['id'], start['sequence']))
        if row['receipt'] is not None:
            path = _ref(root, row['receipt'], 'history failure receipt')
            if row['receipt']['root'] != 'workflow' or path != directory / 'receipt.json':
                _fail('E_ATTEMPT', 'history failure receipt location mismatch')
            receipt = validate_receipt(root, manifest, check, directory, start, require_pass=False)
            if receipt['results'][0]['status'] != 'failed':
                _fail('E_CI', 'history failure is not failed')
        else:
            if (directory / 'receipt.json').exists() or (directory / 'receipt.json').is_symlink():
                _fail('E_ATTEMPT', 'abandoned history now has receipt')
            next_directory, successor = selected(row['successor_start'], check)
            later = [(d, s) for d, s in starts if s['workflow_id'] == manifest['workflow_id']
                     and s['contract_hash'] == contract_hash(manifest) and s['check_ids'] == [check['id']]
                     and s['snapshot_before']['snapshot_id'] == snapshot_id and s['sequence'] > start['sequence']]
            if not later or min(later, key=lambda item: item[1]['sequence'])[0] != next_directory or successor['sequence'] <= start['sequence']:
                _fail('E_ATTEMPT', 'invalid abandoned attempt successor')
    if observed != sorted(set(observed)):
        _fail('E_ATTEMPT', 'history must have unique ordered check/sequence rows')


def _human_snapshot(repo, context, manifest):
    phase = context['state']['phase']
    if phase == 'USER_DECISION_REQUIRED':
        phase = context['state']['stopped_from']
    committed = context['shipping']['commit'] is not None and phase in (_COMMITTED_PHASES | {'COMMIT'})
    return _gate_snapshot(repo, context, manifest, 'commit') if committed else _snapshot(repo, context, manifest)


def human_review_basis(context_path, context, assessment, *, manifest=None, snap=None, retained=None):
    """Generate current approval inputs using the existing quality validators.

    This is deliberately not COMMIT's gate: presentation needs neither shipping
    authorization nor equality with the index. Caller holds the workflow lock.
    """
    cp = Path(context_path).absolute()
    if retained is None:
        manifest = load_contract(cp, context) if manifest is None else manifest
        root, repo = cp.parent.resolve(), repository(context)
        snap = _human_snapshot(repo, context, manifest) if snap is None else snap
        scope = dict(id=context['identity']['workflow_id'], repository=str(repo))
    else:
        manifest = retained['manifest']
        root, repo = retained['workflow_root'], retained['repo_root']
        record = retained.get('human_review') or context.get('execution', {}).get('human_review')
        scope = record['scope'] if record else dict(id=context['identity']['workflow_id'],
            repository=str(Path(context['workspace']['worktree_path'] or context['identity']['source_root']).resolve()))
        if snap is None:
            snap = dict(snapshot_id=manifest['review']['snapshot_id'])
    if retained is None:
        validate_assurance_contract(context, manifest, complete=True)
    elif manifest['version'] == 2 and not manifest['assurance']['adequate_oracle']:
        _fail('E_ASSURANCE', 'adequate oracle is required for completion')
    review = validate_review(root / 'context.json', manifest, snap['snapshot_id'])
    local_receipts = []
    for check in manifest['checks']:
        if check['kind'] == 'gitlab_ci':
            continue
        directory, start = latest_start(root / 'context.json', manifest, check['id'], snap['snapshot_id'])
        receipt = validate_receipt(root, manifest, check, directory, start)
        if retained is None and _input_hashes(root, repo, check) != receipt['inputs_after']:
            _fail('E_EVIDENCE_HASH', 'live inputs differ from local receipt')
        local_receipts.append(dict(check_id=check['id'], receipt=_file_ref(root, directory / 'receipt.json')))
    if retained is None:
        history, pending = _ci_history(root, manifest, snap['snapshot_id'])
    else:
        history = retained['ci_history'] if 'ci_history' in retained else record['presentations'][-1]['basis']['ci_history']
        _validate_retained_ci_history(root, manifest, snap['snapshot_id'], history)
        pending = False  # cleanup already requires all latest CI receipts passed.
    quality = dict(kind='workflow', contract_hash=contract_hash(manifest), review=review, local_receipts=local_receipts)
    if manifest['version'] == 2:
        quality['assurance'] = manifest['assurance']
        quality['assurance_contract'] = assurance_contract(manifest)
    human = _human_module()
    try:
        basis, _ = human.build_basis(scope, dict(base_commit=context['identity']['base_commit'], allowlist=manifest['allowlist'], snapshot_id=snap['snapshot_id']),
            assessment, quality, workflow_root=root, ci_history=history,
            reference_roots=dict(workflow=root, repo=repo))
    except human.HumanReviewError as exc:
        _fail(exc.code, str(exc))
    return basis, pending


def validate_human_review(context_path, context, *, manifest=None, snap=None, retained=None):
    record = context.get('execution', {}).get('human_review')
    if record is None:
        _fail('E_HUMAN_REVIEW_REQUIRED', 'presented user consent is required')
    human = _human_module()
    try:
        human.validate_record_shape(record)
        if record['scope']['id'] != context['identity']['workflow_id'] or any(p['basis']['quality']['kind'] != 'workflow' for p in record['presentations']):
            _fail('E_HUMAN_REVIEW_SCHEMA', 'workflow human review identity/kind mismatch')
        if not record['presentations']:
            _fail('E_HUMAN_REVIEW_REQUIRED', 'presentation required')
        basis, pending = human_review_basis(context_path, context, record['presentations'][-1]['assessment'], manifest=manifest, snap=snap, retained=retained)
        roots = None if retained is None else dict(workflow=retained['workflow_root'], repo=retained['repo_root'])
        result = human.evaluate_human_review(record, workflow_root=Path(context_path).parent if retained is None else retained['workflow_root'],
                                            current_basis=basis, reference_roots=roots)
    except human.HumanReviewError as exc:
        _fail(exc.code, str(exc))
    if result['status'] != 'passed':
        _fail('E_HUMAN_REVIEW_STALE' if result['status'] == 'stale' else 'E_HUMAN_REVIEW_REQUIRED', result['reason'])
    return result


def human_review_command(context_path, *, operation=None, expected_revision=None):
    """CLI adapter: all workflow changes use the existing directory-lock CAS."""
    cp = Path(context_path).absolute()
    spec = importlib.util.spec_from_file_location('human_review_state', Path(__file__).with_name('workflow_state.py'))
    state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state)
    human = _human_module()
    result = None
    def inputs(context, selected):
        phase = context['state']['phase']
        if phase == 'USER_DECISION_REQUIRED':
            phase = context['state']['stopped_from']
        retained = resolve_cleanup_evidence(cp, context, require_record_match=False) if phase in _CLEANUP_PHASES else None
        basis, pending = human_review_basis(cp, context, selected, retained=retained)
        roots = None if retained is None else dict(workflow=retained['workflow_root'], repo=retained['repo_root'])
        return basis, pending, roots
    def evaluate(context):
        record = context.get('execution', {}).get('human_review')
        if record is None or not record['presentations']:
            return dict(route='self', status='pending', reason='E_HUMAN_REVIEW_REQUIRED: presentation required', presentation_id=None, prompt='')
        basis, _, roots = inputs(context, record['presentations'][-1]['assessment'])
        return human.evaluate_human_review(record, workflow_root=cp.parent, current_basis=basis, reference_roots=roots)
    if operation is None:
        try:
            with _lock(cp.parent):
                return evaluate(state.load_context(cp))
        except state.StateError as exc:
            _fail('E_HUMAN_REVIEW_SCHEMA', str(exc))
    if expected_revision is None:
        _fail('E_HUMAN_REVIEW_SCHEMA', 'expected-revision is required')
    def update(context):
        nonlocal result
        record = context['execution'].get('human_review')
        if not isinstance(operation, dict):
            _fail('E_HUMAN_REVIEW_SCHEMA', 'operation must be an object')
        selected = operation.get('assessment') if operation.get('action') == 'present' else (
            record['presentations'][-1]['assessment'] if record and record['presentations'] else None)
        negative = operation.get('action') == 'revoke' or (
            operation.get('action') == 'respond' and operation.get('decision') == 'request_change')
        # Negative responses revoke permission even when the underlying quality
        # evidence is stale or unavailable. apply_operation still validates the
        # exact operation, latest presentation, targets, citation and revision.
        basis, pending, roots = (None, False, None) if negative else inputs(context, selected)
        updated = human.apply_operation(record, operation, expected_revision=record['revision'] if record else 0,
                                       workflow_root=cp.parent, current_basis=basis, ci_pending=pending, reference_roots=roots)
        context['execution']['human_review'] = updated
        result = human.evaluate_human_review(updated, workflow_root=cp.parent, current_basis=basis, reference_roots=roots)
        # Presentation/partial answers/revocation remain a durable stop. In
        # particular a completed phase cannot keep its completed state on revoke.
        if result['status'] != 'passed' and context['state']['phase'] != 'USER_DECISION_REQUIRED':
            if context['state']['phase'] == 'ARTIFACT_REMOVE':
                context['state'].update(phase='USER_DECISION_REQUIRED', stopped_from='ARTIFACT_REMOVE')
            else:
                state.stop_context(context, result['reason'])
        return context
    try:
        state.mutate_context(cp, expected_revision=expected_revision, operation=update)
    except (state.StateError, human.HumanReviewError) as exc:
        _fail('E_HUMAN_REVIEW_RESPONSE', str(exc))
    return result


def _export_refs(manifest):
    refs = [manifest['source']]
    for entry in manifest['active']:
        refs.extend(entry[field] for field in ('oracle', 'plan', 'task'))
    if manifest['ci'] is not None:
        refs.append(manifest['ci']['authorization_ref'])
    if manifest['review'] is not None:
        refs.append(dict(root='workflow', path=manifest['review']['path'], sha256=manifest['review']['hash']))
    return refs


def export_evidence(context_path, output):
    """Copy the selected evidence into two relocatable roots, without publishing."""
    cp = Path(context_path).absolute()
    root = cp.parent.resolve()
    output = Path(output).absolute()
    with _lock(root):
        context = _json(cp)
        phase = context['state']['phase']
        if phase == 'USER_DECISION_REQUIRED':
            phase = context['state']['stopped_from']
        retained = resolve_cleanup_evidence(cp, context, require_record_match=False) if phase in _CLEANUP_PHASES else None
        manifest = retained['manifest'] if retained else load_contract(cp, context)
        repo = retained['repo_root'] if retained else repository(context)
        review = validate_review(cp, manifest)
        validate_human_review(cp, context, manifest=manifest, retained=retained)
        record = context['execution']['human_review']
        human = _human_module()
        basis = record['presentations'][-1]['basis']
        selected = [latest_start(cp, manifest, c['id'], review['snapshot_id']) for c in manifest['checks']]
        for row in basis['ci_history']:
            for key in ('start', 'successor_start'):
                if row[key] is not None:
                    path = _ref(root, row[key], 'history export')
                    selected.append((path.parent, _json(path)))
        selected = sorted({start['run_id']: (directory, start) for directory, start in selected}.values(), key=lambda item: item[1]['sequence'])
        if output.exists() or output.is_symlink() or any(p.is_symlink() for p in output.parents):
            _fail('E_EVIDENCE_PATH', 'export requires a new directory without symlink parents')
        output.mkdir(parents=True)
        for name in ('workflow', 'repo'):
            (output / name).mkdir()
        def copy_file(source, destination):
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if destination.read_bytes() != source.read_bytes():
                    _fail('E_EVIDENCE_HASH', 'conflicting export references')
            else:
                shutil.copyfile(source, destination)
        copy_file(root / 'evidence.json', output / 'workflow' / 'evidence.json')
        _atomic_new(output / 'workflow' / 'human-review.json', record)
        for ref in [*_export_refs(manifest), *human.iter_references(basis)]:
            base = root if ref['root'] == 'workflow' else repo
            source = _ref(base, ref, 'export reference', oracle='locator' in ref)
            copy_file(source, output / ref['root'] / ref['path'])
        for directory, start in selected:
            prefix = directory.relative_to(root)
            copy_file(directory / 'start.json', output / 'workflow' / prefix / 'start.json')
            if (directory / 'receipt.json').exists() or (directory / 'receipt.json').is_symlink():
                receipt = _json(directory / 'receipt.json')
                copy_file(directory / 'receipt.json', output / 'workflow' / prefix / 'receipt.json')
                for ref in receipt['files']:
                    if ref.get('root') != 'workflow':
                        _fail('E_EVIDENCE_PATH', 'raw file root must be workflow')
                    source = _ref(root, ref, 'export raw file')
                    if source.parent != directory:
                        _fail('E_EVIDENCE_PATH', 'raw file outside its run')
                    copy_file(source, output / 'workflow' / ref['path'])
        validate_export(output)
        return dict(output=str(output), run_ids=[s['run_id'] for _, s in selected])


def _validate_export_quality(output):
    """Validate retained review and latest successful receipts, before consent.

    Legacy bundles can supply quality for a first presentation. This primitive
    does not authorize cleanup; validate_export remains the completion gate.
    """
    output = Path(output).absolute()
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        _fail('E_EVIDENCE_PATH', 'symlink export root')
    root = _path(output, 'workflow', 'workflow root', directory=True)
    repo = _path(output, 'repo', 'repo root', directory=True)
    recorded = _json(root / 'evidence.json')
    manifest = _load_manifest(root, repo, recorded.get('workflow_id'), retained=True)
    review = validate_review(root / 'context.json', manifest)
    for check in manifest['checks']:
        directory, start = latest_start(root / 'context.json', manifest, check['id'], review['snapshot_id'])
        if start['check_ids'] != [check['id']] or any(start[key] != check[key] for key in ('kind', 'argv', 'cwd')) or start['inputs_before'] != check['inputs']:
            _fail('E_ATTEMPT', 'export start does not match check')
        validate_receipt(root, manifest, check, directory, start)
    return dict(manifest=manifest, workflow_root=root, repo_root=repo)


def validate_export(output):
    """Validate quality and consent using bundle roots, never live Git."""
    retained = _validate_export_quality(output)
    manifest, root, repo = retained['manifest'], retained['workflow_root'], retained['repo_root']
    record = _json(root / 'human-review.json')
    human = _human_module()
    try:
        human.validate_record_shape(record)
        if record['scope']['id'] != manifest['workflow_id'] or not record['presentations'] or any(p['basis']['quality']['kind'] != 'workflow' for p in record['presentations']):
            _fail('E_HUMAN_REVIEW_SCHEMA', 'retained record identity/kind mismatch')
        p = record['presentations'][-1]
        retained = dict(manifest=manifest, workflow_root=root, repo_root=repo, human_review=record)
        # The fixed base and scope remain part of the record; only Ref roots relocate.
        context = dict(identity=dict(workflow_id=manifest['workflow_id'], base_commit=p['target']['base_commit']), execution=dict(human_review=record))
        validate_human_review(root / 'context.json', context, retained=retained)
    except human.HumanReviewError as exc:
        _fail(exc.code, str(exc))
    return retained


def resolve_cleanup_evidence(context_path, context, *, require_record_match=True):
    cp = Path(context_path).absolute()
    bundle = _path(cp.parent.resolve(), 'evidence/cleanup', 'cleanup export', directory=True)
    recorded_consent = bundle / 'workflow' / 'human-review.json'
    if require_record_match or recorded_consent.exists() or recorded_consent.is_symlink():
        retained = validate_export(bundle)
    else:
        retained = _validate_export_quality(bundle)
    current = _json(cp.parent / 'evidence.json')
    manifest = retained['manifest']
    if require_record_match and context.get('execution', {}).get('human_review') != retained['human_review']:
        _fail('E_HUMAN_REVIEW_STALE', 'cleanup record differs from authoritative human review')
    record = retained.get('human_review')
    history, _ = _ci_history(cp.parent.resolve(), manifest, manifest['review']['snapshot_id'])
    if record is not None and history != record['presentations'][-1]['basis']['ci_history']:
        _fail('E_HUMAN_REVIEW_STALE', 'cleanup CI history differs from authoritative attempts')
    if record is None:
        _validate_retained_ci_history(retained['workflow_root'], manifest, manifest['review']['snapshot_id'], history)
        retained['ci_history'] = history
    if not require_record_match:
        fixed = _gate_snapshot(Path(context['identity']['source_root']), context, manifest, 'commit')
        validate_review(retained['workflow_root'] / 'context.json', manifest, fixed['snapshot_id'])
    if current != manifest or manifest['workflow_id'] != context['identity']['workflow_id']:
        _fail('E_EVIDENCE_HASH', 'cleanup contract/review differs from authoritative evidence')
    for check in manifest['checks']:
        _, start = latest_start(cp, manifest, check['id'], manifest['review']['snapshot_id'])
        _, copied = latest_start(retained['workflow_root'] / 'context.json', manifest, check['id'], manifest['review']['snapshot_id'])
        if start != copied:
            _fail('E_ATTEMPT', 'cleanup retained attempt differs from latest start')
        if not require_record_match and check['kind'] == 'gitlab_ci':
            directory = retained['workflow_root'] / 'evidence' / 'runs' / copied['run_id']
            validate_ci_receipt(retained['workflow_root'], manifest, check, directory, copied, context['shipping']['commit'])
    return retained
