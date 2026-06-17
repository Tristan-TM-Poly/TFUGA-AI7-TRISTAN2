#!/usr/bin/env python3
"""Generate a safe OAK/CVCD repository report.

This script only reads repository files and writes reports/autopilot/*.json and
*.md. It does not open network connections and does not execute shell commands.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

IGNORE = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache'}


def iter_files(root: pathlib.Path):
    for path in root.rglob('*'):
        rel = path.relative_to(root)
        if any(part in IGNORE for part in rel.parts):
            continue
        if path.is_file():
            yield rel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', default='.')
    parser.add_argument('--mode', default='scan')
    args = parser.parse_args()

    root = pathlib.Path(args.repo_root).resolve()
    files = list(iter_files(root))
    suffix_counts = {}
    for rel in files:
        suffix = rel.suffix or '[no_suffix]'
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

    capabilities = {
        'has_tests': (root / 'tests').exists(),
        'has_docs': (root / 'docs').exists(),
        'has_schemas': (root / 'schemas').exists(),
        'has_workflows': (root / '.github' / 'workflows').exists(),
        'has_pyproject': (root / 'pyproject.toml').exists(),
        'has_requirements': (root / 'requirements.txt').exists(),
    }

    m_minus = []
    if not capabilities['has_tests']:
        m_minus.append({'type': 'missing_tests', 'severity': 'medium'})
    if not (capabilities['has_pyproject'] or capabilities['has_requirements']):
        m_minus.append({'type': 'missing_dependency_manifest', 'severity': 'medium'})

    report = {
        'generated_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        'mode': args.mode,
        'github_repository': os.environ.get('GITHUB_REPOSITORY'),
        'github_ref': os.environ.get('GITHUB_REF_NAME'),
        'github_sha': os.environ.get('GITHUB_SHA'),
        'python': sys.version,
        'file_count': len(files),
        'suffix_counts': dict(sorted(suffix_counts.items(), key=lambda x: (-x[1], x[0]))),
        'capabilities': capabilities,
        'm_minus': m_minus,
        'next_actions': [
            'Keep generated changes on branches and pull requests.',
            'Add tests for canon modules before promoting claims.',
            'Register the home runner with labels self-hosted, linux, x64, home-lab.',
        ],
    }

    out = root / 'reports' / 'autopilot'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'autonomous_build_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    md = ['# Autonomous Build Report', '', f"Generated: {report['generated_at']}", '', '## M_MINUS']
    md.extend([f"- {item['severity']} / {item['type']}" for item in m_minus] or ['- none'])
    (out / 'autonomous_build_report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    (out / 'm_minus_latest.json').write_text(json.dumps(m_minus, indent=2) + '\n', encoding='utf-8')
    print('wrote reports/autopilot outputs')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
