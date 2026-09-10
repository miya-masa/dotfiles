"""Controller-assessed fixtures exercise routing/rendering/gating, not LLM accuracy."""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.workflow_core.test_human_review import change, card, cli, present, response, hr

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = 'claude'


def test_local_judgment_routing(change):
    selected = change['op']['assessment']
    selected['cards'] = [card(change)]
    assert hr.classify_assessment(selected) == 'human'
    record = present(change)
    prompt = record['presentations'][-1]['prompt']
    for text in ('process', 'changed', '障害時', '影響', 'inline', 'helper', '回答の効力'):
        assert text in prompt
    assert cli(change).returncode == 1
    assert cli(change, response(record, ['card-1']), 1).returncode == 0
    # Each missing condition rejects a new completion presentation, not just a label.
    for index in range(5):
        bad = copy.deepcopy(change['op']); bad.pop('scope')
        bad['assessment']['cards'][0]['conditions'][index]['satisfied'] = False
        before = change['path'].read_bytes()
        assert cli(change, bad, 2).returncode != 0
        assert change['path'].read_bytes() == before


@pytest.mark.parametrize('concern', ['high risk', 'AIの不安', '既存規約で決まる', 'styleの好み', '単に二案がある'])
def test_nonhuman_concerns_do_not_request_code_review(change, concern):
    selected = change['op']['assessment']
    selected['self_reason'] = concern + 'だけでは人間固有の局所判断はない。規約と証拠で解消済み。'
    if concern == 'high risk':
        # Human self consent does not remove the required fresh AI review.
        change['op']['quality']['review_requirement']['fresh_count'] = 1
        change['op']['quality']['reviews'][0].update(id='fresh-1', kind='fresh')
    assert hr.classify_assessment(selected) == 'self'
    record = present(change)
    prompt = record['presentations'][-1]['prompt']
    assert '人間コードレビュー対象なし' in prompt
    assert 'セルフレビューで通してください' in prompt
    assert '各カード' not in prompt
    assert cli(change).returncode == 1
    assert cli(change, response(record), 1).returncode == 0


@pytest.mark.parametrize('kind,route', [('bug', 'fix'), ('test_gap', 'verify'), ('environment', 'verify'),
                                        ('technical_disagreement', 'diagnose'), ('specification', 'specification')])
def test_blockers_route_to_fix_verify_diagnose_or_specification(change, kind, route):
    selected = change['op']['assessment']
    selected['blockers'] = [dict(kind=kind, reason='再現ログが示す未解決事項', evidence=[change['proof']])]
    # A plausible local card must not turn a missing test/environment into consent.
    selected['cards'] = [card(change)]
    assert hr.classify_assessment(selected) == route
    result = cli(change, change['op'], 0)
    assert result.returncode != 0
    assert not change['path'].exists()
    assert route in result.stderr


def test_runtime_entrypoints_link_to_shared_human_review_contract():
    common = ROOT / 'dot_agents/workflows/software_delivery/references/review-common.md'
    evidence = common.with_name('evidence-contract.md')
    assert common.is_file() and evidence.is_file()
    entrypoints = [ROOT / f'dot_{RUNTIME}' / ('AGENTS.md' if RUNTIME == 'codex' else 'CLAUDE.md'),
                  ROOT / 'dot_agents/skills/task/SKILL.md', ROOT / 'dot_agents/skills/bugfix/SKILL.md',
                  common.with_name('effort-policy.md')]
    entrypoints += [ROOT / f'dot_{RUNTIME}/skills/{name}/SKILL.md' for name in ('execute-plan', 'ship-change', 'execute-and-ship')]
    if RUNTIME == 'codex':
        entrypoints += [ROOT / 'dot_codex/review-policy.md']
        references = [ROOT / f'dot_codex/workflows/software_delivery/references/{name}.md' for name in ('task-execution', 'state-recovery', 'post-merge-cleanup')]
    else:
        references = [ROOT / 'dot_claude/skills/execute-plan/references/task-execution.md',
                      ROOT / 'dot_claude/skills/execute-plan/references/state-and-artifacts.md',
                      ROOT / 'dot_claude/skills/ship-change/references/shipping.md']
    for path in entrypoints:
        text = path.read_text()
        assert 'review-common.md' in text, path
        assert '人間' in text and '承認' in text, path
    for path in references:
        text = path.read_text()
        assert 'evidence-contract.md' in text and 'human_review.py' in text, path
    shared = common.read_text()
    assert shared.index('| リスク |') < shared.index('## 人間コードレビュー')
    assert 'evidence-contract.md#人間レビューの記録と操作' in shared
    protocol = evidence.read_text()
    for identifier in ('--operation-file', '--expected-revision', 'approve_current', 'request_change', 'revoke',
                       'git-path', 'review_requirement', 'fresh_count', 'verification_assumptions', 'user_citation'):
        assert identifier in protocol


def test_documented_direct_operation_builder_matches_real_cli(change):
    document = (ROOT / 'dot_agents/workflows/software_delivery/references/evidence-contract.md').read_text()
    source = re.search(r"python3 - \"\$review_repo\".*?<<'PY'\n(.*?)\nPY", document, re.S).group(1)
    for name in ('assessment', 'quality'):
        (change['tmp'] / (name + '.json')).write_text(json.dumps(change['op'][name]))
    (change['tmp'] / 'allowlist.json').write_text(json.dumps(change['op']['target']['allowlist']))
    built = subprocess.run([sys.executable, '-', str(change['repo']), change['op']['scope']['id'],
                            change['op']['target']['base_commit']], input=source, cwd=change['tmp'],
                           capture_output=True, text=True, check=True)
    result = cli(change, json.loads(built.stdout), 0)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['status'] == 'pending'
