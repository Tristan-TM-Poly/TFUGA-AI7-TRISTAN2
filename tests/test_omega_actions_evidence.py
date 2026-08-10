from __future__ import annotations

from pathlib import Path

from omega_actions_t.evidence import build_evidence_bundle, render_markdown


def test_evidence_bundle_fuses_static_delta_and_telemetry(tmp_path: Path) -> None:
    workflow = tmp_path / '.github' / 'workflows' / 'ci.yml'
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        """
name: CI
on:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pip install pytest
      - run: pytest -q
""".strip() + "\n",
        encoding='utf-8',
    )
    telemetry = {
        'workflow_runs': [
            {
                'id': 1,
                'name': 'CI',
                'head_branch': 'feature',
                'status': 'completed',
                'conclusion': 'success',
                'created_at': '2026-08-09T10:00:00Z',
                'run_started_at': '2026-08-09T10:00:10Z',
                'updated_at': '2026-08-09T10:02:10Z',
                'jobs': [],
            }
        ]
    }

    bundle = build_evidence_bundle(
        tmp_path,
        changed_files=['src/core.py'],
        telemetry_payload=telemetry,
    )

    assert bundle['evidence_state'] == 'MEASURED_BASELINE_READY'
    assert len(bundle['optimization_candidates']) == 1
    candidate = bundle['optimization_candidates'][0]
    assert candidate['workflow'] == '.github/workflows/ci.yml'
    assert candidate['broad_unrouted'] is True
    assert candidate['run_count_sample'] == 1
    assert candidate['duration_p95_seconds'] == 120.0
    assert bundle['oak_gates']['automatic_rewrite_authorized'] is False
    assert 'Evidence Bundle' in render_markdown(bundle)
