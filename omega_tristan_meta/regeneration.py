from pathlib import Path
from typing import Dict
import hashlib, json

def build_manifest(root: Path, relative_paths) -> Dict[str, str]:
    return {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in sorted(relative_paths)}

def verify_manifest(root: Path, manifest: Dict[str, str]):
    failures = {}
    for rel, expected in manifest.items():
        p = root / rel
        if not p.exists():
            failures[rel] = "missing"
            continue
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected:
            failures[rel] = {"expected": expected, "actual": actual}
    return failures

def load_book0(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
