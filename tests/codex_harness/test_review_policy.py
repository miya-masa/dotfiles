import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
POLICY = (ROOT / "dot_codex/review-policy.md").read_text(encoding="utf-8")
PLANNING_SKILL = (ROOT / "dot_codex/skills/implementation-planning/SKILL.md").read_text(encoding="utf-8")
RESULT_SCHEMA = json.loads(
    (ROOT / "tests/codex_harness/fixtures/routing_eval/v1/result.schema.json").read_text(encoding="utf-8")
)


def test_review_matrix_cardinality_and_unknown_promotion() -> None:
    for phrase in (
        "independent-risk", "reviewer 2体", "high", "reviewer 1体",
        "minor", "reviewer 0", "normal", "判定できない場合はminorへ落とさず",
    ):
        assert phrase in POLICY


def test_review_matrix_is_deterministic_for_full_input_and_output_tuple() -> None:
    compact = " ".join(POLICY.split())
    for phrase in (
        "artifact_kind, normalized_trigger_set, dependency_cone, active_ac_set",
        "tier, reviewer_count, role, model, lenses, scope, failure_route",
        "triggerは下記の順に正規化",
        "入力順や反復で結果を変えない",
    ):
        assert phrase in compact


def test_independent_risk_reviewers_have_non_overlapping_lenses() -> None:
    assert "相互に重複しないlens" in POLICY
    assert "1 reviewerあたり最大2 lens" in POLICY


def test_canonical_lens_vocabulary_matches_artifact_mappings_schema_and_skill() -> None:
    canonical_match = re.search(r"canonical lens集合は \*\*(.+?)\*\* とする", POLICY)
    assert canonical_match is not None
    canonical = set(canonical_match.group(1).split(" / "))
    schema = set(RESULT_SCHEMA["properties"]["lenses"]["items"]["enum"])
    assert canonical == schema

    mapping_line = next(line for line in POLICY.splitlines() if line.startswith("artifact別の候補は"))
    mapped = {
        lens
        for group in re.findall(r"`([^`]+)`", mapping_line)[:4]
        for lens in group.split(" / ")
    }
    assert mapped <= canonical
    assert {"Spec compliance", "Feasibility", "Simplicity"} <= canonical
    assert all(lens in PLANNING_SKILL for lens in ("Spec compliance", "Feasibility", "Simplicity"))
