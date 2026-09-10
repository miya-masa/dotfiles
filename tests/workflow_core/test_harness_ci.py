from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/testing-harness.yml"
COMMAND = "python3 -m pytest tests/workflow_core tests/codex_harness tests/claude_harness --junitxml=.aidocs/harness-results/junit.xml"


def test_ci_runs_shared_harness_command_and_uploads_results_on_failure() -> None:
    body = WORKFLOW.read_text(encoding="utf-8")
    assert COMMAND in body
    assert "if: always()" in body
    assert "harness-results" in body
    assert "upload-artifact@v7" in body
    assert "include-hidden-files: true" in body
    assert "actions/checkout@v7" in body
    assert "actions/setup-python@v7" in body
    assert "contents: read" in body
