from __future__ import annotations
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tristan_omni_core.core.models import ProbeResult


def probe_one(module):
    start = time.time()
    path = Path(module.path)
    files = list(path.rglob('*')) if path.exists() else []
    py_count = sum(1 for p in files if p.is_file() and p.suffix == '.py')
    md_count = sum(1 for p in files if p.is_file() and p.suffix.lower() == '.md')
    json_count = sum(1 for p in files if p.is_file() and p.suffix.lower() == '.json')
    checks = {
        'exists': path.exists(),
        'has_readme': (path / 'README.md').exists(),
        'has_tests': (path / 'tests' / 'test_smoke.py').exists(),
        'has_reports': any('reports' in p.parts for p in files if p.is_file()),
        'has_python': py_count > 0,
        'has_markdown': md_count > 0,
    }
    risks = []
    if not checks['exists']:
        risks.append('module path missing')
    if not checks['has_tests']:
        risks.append('no smoke test found')
    status = 'passed' if checks['exists'] else 'needs_review'
    return ProbeResult(module.id, status, time.time() - start, checks, {
        'file_count': sum(1 for p in files if p.is_file()),
        'py_count': py_count,
        'md_count': md_count,
        'json_count': json_count,
        'score_omega': module.score_omega(),
    }, risks)


def run_parallel_probes(modules, max_workers=12):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(probe_one, m) for m in modules]
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda r: r.module_id)
