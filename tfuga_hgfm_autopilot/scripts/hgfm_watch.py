from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

BLOCKED_NAMES = {'.env', '.env.local'}
BLOCKED_SUFFIXES = {'.pem', '.key', '.p12', '.sqlite', '.db'}
MAX_FILE_MB = 25


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def changed_files(repo: Path) -> list[Path]:
    result = run(['git', 'status', '--porcelain'], repo)
    files: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path_text = line[3:].strip()
        if ' -> ' in path_text:
            path_text = path_text.split(' -> ', 1)[1]
        files.append(repo / path_text)
    return files


def is_blocked(path: Path) -> bool:
    name = path.name.lower()
    if name in BLOCKED_NAMES:
        return True
    if path.suffix.lower() in BLOCKED_SUFFIXES:
        return True
    if path.exists() and path.is_file():
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_MB:
            return True
    return False


def has_danger(repo: Path, files: list[Path]) -> list[str]:
    dangers: list[str] = []
    markers = ['PRIVATE KEY', 'API_KEY=', 'TOKEN=', 'PASSWORD=']
    for file in files:
        rel = file.relative_to(repo) if str(file).startswith(str(repo)) else file
        if is_blocked(file):
            dangers.append(f'blocked file: {rel}')
        if file.exists() and file.is_file():
            text = file.read_text(errors='ignore')[:200000]
            upper = text.upper()
            for marker in markers:
                if marker in upper:
                    dangers.append(f'sensitive marker in: {rel}')
                    break
    return dangers


def run_tests(repo: Path) -> bool:
    if (repo / 'tests').exists():
        result = run(['python', '-m', 'pytest', '-q'], repo, check=False)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return False
    validator = repo / 'tristan2_meta_os.py'
    if validator.exists():
        result = run(['python', 'tristan2_meta_os.py', '--auto-validate-atsc14'], repo, check=False)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return False
    return True


def commit_once(repo: Path, push: bool, dry_run: bool) -> None:
    files = changed_files(repo)
    if not files:
        print('HGFM stable: no git entropy detected.')
        return
    dangers = has_danger(repo, files)
    if dangers:
        print('Commit cancelled: guard detected risk.')
        for danger in dangers:
            print(f'- {danger}')
        return
    if dry_run:
        print('Dry run: changes detected and guards passed.')
        for file in files:
            print(f'- {file.relative_to(repo)}')
        return
    if not run_tests(repo):
        print('Commit cancelled: tests failed.')
        return
    run(['git', 'add', '.'], repo)
    staged = run(['git', 'diff', '--cached', '--name-only'], repo).stdout.strip()
    if not staged:
        print('Nothing staged after filtering.')
        return
    run(['git', 'commit', '-m', 'auto-factorisation(HGFM): controlled sync'], repo)
    if push:
        branch = run(['git', 'branch', '--show-current'], repo).stdout.strip()
        if not branch:
            print('Push cancelled: no branch detected.')
            return
        run(['git', 'push', 'origin', branch], repo)
        print(f'Pushed to origin/{branch}.')
    else:
        print('Local commit done. Push not enabled.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('repo')
    parser.add_argument('--interval', type=int, default=3600)
    parser.add_argument('--push', action='store_true')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / '.git').exists():
        raise SystemExit(f'Not a git repository: {repo}')
    if args.once:
        commit_once(repo, args.push, args.dry_run)
        return
    while True:
        commit_once(repo, args.push, args.dry_run)
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
