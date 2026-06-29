#!/usr/bin/env python3
"""HGFM Symbiotic Migration v0.1.

Autonomous local-first migrator for legacy Raman spectra, Python scripts,
and lightweight text/LaTeX/Markdown notes. Designed for GitHub Actions demos
and local execution without destructive side effects.
"""
from __future__ import annotations

import argparse
import ast
import csv
import glob
import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Iterable

import numpy as np
import pandas as pd


STATUS = "S2"
TRUTH_LEVEL = "T1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


@dataclass
class DCTPPPacket:
    packet_id: str
    status: str
    truth_level: str
    created_at: str
    source_path: str
    source_sha256: str
    output_path: str
    metrics: dict
    claims: list
    risks: list
    next_tests: list

    def to_dict(self) -> dict:
        return asdict(self)


def detect_columns(df: pd.DataFrame) -> tuple[str, str]:
    aliases_x = ["raman_shift", "wavenumber", "cm-1", "cm^-1", "shift", "x"]
    aliases_y = ["intensity", "counts", "signal", "absorbance", "y"]
    lower = {str(c).lower().strip(): c for c in df.columns}
    x_col = next((lower[a] for a in aliases_x if a in lower), None)
    y_col = next((lower[a] for a in aliases_y if a in lower), None)
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if x_col is None and numeric:
        x_col = numeric[0]
    if y_col is None and len(numeric) >= 2:
        y_col = numeric[1]
    if x_col is None or y_col is None:
        raise ValueError("Could not infer spectral x/y columns")
    return x_col, y_col


def moving_median(y: np.ndarray, size: int = 5) -> np.ndarray:
    size = max(3, int(size) | 1)
    pad = size // 2
    yp = np.pad(y, pad, mode="edge")
    return np.array([np.median(yp[i:i + size]) for i in range(len(y))], dtype=float)


def moving_average(y: np.ndarray, size: int = 11) -> np.ndarray:
    size = max(3, int(size) | 1)
    if len(y) < size:
        return y.copy()
    kernel = np.ones(size) / size
    yp = np.pad(y, size // 2, mode="edge")
    return np.convolve(yp, kernel, mode="valid")


def remove_cosmic_spikes(y: np.ndarray, z_threshold: float = 8.0) -> tuple[np.ndarray, int]:
    med = moving_median(y, 5)
    resid = y - med
    mad = np.median(np.abs(resid - np.median(resid)))
    sigma = 1.4826 * mad if mad > 1e-12 else np.std(resid)
    if sigma <= 1e-12:
        return y.copy(), 0
    mask = np.abs(resid) / sigma > z_threshold
    out = y.copy()
    out[mask] = med[mask]
    return out, int(mask.sum())


def baseline_percentile(y: np.ndarray, window: int = 51, percentile: float = 5.0) -> np.ndarray:
    window = max(5, int(window) | 1)
    pad = window // 2
    yp = np.pad(y, pad, mode="edge")
    return np.array([np.percentile(yp[i:i + window], percentile) for i in range(len(y))], dtype=float)


def compute_auc(x: np.ndarray, y: np.ndarray, normalize: bool = True) -> dict:
    order = np.argsort(x)
    xs = x[order]
    ys = np.maximum(y[order], 0.0)
    auc = float(np.trapezoid(ys, xs))
    span = float(xs[-1] - xs[0]) if len(xs) > 1 else 0.0
    return {
        "auc": auc,
        "auc_norm": float(auc / span) if normalize and span > 0 else auc,
        "x_min": float(xs[0]),
        "x_max": float(xs[-1]),
    }


def process_spectrum(path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(path)
    x_col, y_col = detect_columns(df)
    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(df[y_col], errors="coerce").to_numpy(dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3:
        raise ValueError(f"not enough valid points in {path}")
    y_despiked, spikes = remove_cosmic_spikes(y)
    baseline = baseline_percentile(y_despiked)
    corrected = y_despiked - baseline
    smooth = moving_average(corrected)
    metrics = compute_auc(x, smooth)
    metrics.update({
        "points": int(len(x)),
        "cosmic_spikes_replaced": int(spikes),
        "raw_intensity_mean": float(np.mean(y)),
        "corrected_intensity_mean": float(np.mean(smooth)),
    })
    stem = path.stem
    csv_out = out_dir / f"{stem}.hgfm_unified.csv"
    packet_out = out_dir / f"{stem}.dctpp.json"
    pd.DataFrame({
        "raman_shift": x,
        "intensity_raw": y,
        "intensity_despiked": y_despiked,
        "baseline": baseline,
        "intensity_corrected": corrected,
        "intensity_smooth": smooth,
    }).to_csv(csv_out, index=False)
    packet = DCTPPPacket(
        packet_id=f"DCTPP-SPECTRUM-{stem}",
        status=STATUS,
        truth_level=TRUTH_LEVEL,
        created_at=utc_now(),
        source_path=str(path),
        source_sha256=sha256_file(path),
        output_path=str(csv_out),
        metrics=metrics,
        claims=[{"claim": "Legacy spectrum migrated to HGFM AUC format", "status": "computed-local"}],
        risks=[
            "Column inference can fail on ambiguous CSVs.",
            "Baseline parameters require instrument calibration.",
            "AUC claims require replicate uncertainty before publication.",
        ],
        next_tests=["Run on real replicates", "Bootstrap uncertainty", "Compare AUC to peak-height ratios"],
    )
    write_json(packet_out, packet.to_dict())
    return {"input": str(path), "csv": str(csv_out), "packet": str(packet_out), "metrics": metrics}


def scan_python_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    functions, classes, imports = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({"name": node.name, "line": node.lineno, "args": [a.arg for a in node.args.args]})
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.get_source_segment(text, node) or "")
    names = " ".join([f["name"] for f in functions] + [c["name"] for c in classes]).lower()
    suggestions = []
    if any(k in names for k in ["spectrum", "baseline", "smooth", "auc", "peak"]):
        suggestions.append("Move spectral processing to core/spectra.py")
    if any(k in names for k in ["plot", "figure", "dashboard", "ui"]):
        suggestions.append("Move UI/visualization to dashboard/viz module")
    if len(functions) > 8:
        suggestions.append("Split function-heavy script by responsibility")
    if not suggestions:
        suggestions.append("Keep as utility until usage graph is known")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "lines": len(text.splitlines()),
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(imports)),
        "refactor_suggestions": suggestions,
    }


def split_sections(text: str) -> list[tuple[str, str]]:
    pat = re.compile(r"(?m)^(\\section\{.*?\}|\\subsection\{.*?\}|#{1,3}\s+.*)$")
    matches = list(pat.finditer(text))
    if not matches:
        return [("untitled", text)]
    out = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((match.group(1), text[start:end].strip()))
    return out


def fuse_docs(paths: Iterable[Path], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    keywords = ["TFUGA", "HGFM", "Raman", "AUC", "AT-SC-14", "SYNERGIE-T3", "DCT++"]
    candidates = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for title, body in split_sections(text):
            hits = [k for k in keywords if k.lower() in body.lower()]
            if hits:
                candidates.append({
                    "source": str(path),
                    "source_sha256": sha256_file(path),
                    "title": title,
                    "keywords": hits,
                    "excerpt": body[:2000],
                })
    tex_lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\begin{document}",
        r"\section*{HGFM Symbiotic Fusion Stub}",
        "Generated from legacy notes. Review before canonization.",
    ]
    for i, c in enumerate(candidates, 1):
        body = c["excerpt"].replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
        tex_lines += [f"\\section*{{Imported Block {i}}}", f"Source: {c['source']}", body]
    tex_lines.append(r"\end{document}")
    tex_path = out_dir / "hgfm_fused_stub.tex"
    tex_path.write_text("\n\n".join(tex_lines), encoding="utf-8")
    manifest = {
        "created_at": utc_now(),
        "status": STATUS,
        "truth_level": TRUTH_LEVEL,
        "candidate_count": len(candidates),
        "output": str(tex_path),
        "candidates": candidates,
        "risks": ["Manual cleaning required", "Historical coherence is not proof"],
    }
    write_json(out_dir / "latex_fusion_manifest.json", manifest)
    return manifest


def expand(patterns: list[str] | None) -> list[Path]:
    if not patterns:
        return []
    paths = []
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            paths += [Path(h) for h in hits]
        elif Path(pat).exists():
            paths.append(Path(pat))
    return sorted(set(paths))


def run_migration(args: argparse.Namespace) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spectra = expand(args.spectra)
    code = expand(args.code)
    docs = expand(args.docs)
    manifest = {
        "created_at": utc_now(),
        "status": STATUS,
        "truth_level": TRUTH_LEVEL,
        "mode": "local-first",
        "inputs": {"spectra": list(map(str, spectra)), "code": list(map(str, code)), "docs": list(map(str, docs))},
        "outputs": {},
        "gates": {
            "human_review_required_before_push": True,
            "human_review_required_before_deploy": True,
            "raw_data_sent_to_vercel": False,
        },
    }
    if spectra:
        manifest["outputs"]["spectra"] = [process_spectrum(p, out / "spectra") for p in spectra]
    if code:
        inventory = {"created_at": utc_now(), "status": STATUS, "files": [scan_python_file(p) for p in code]}
        write_json(out / "code_inventory.json", inventory)
        manifest["outputs"]["code_inventory"] = str(out / "code_inventory.json")
    if docs:
        manifest["outputs"]["docs"] = fuse_docs(docs, out / "docs")
    write_json(out / "hgfm_migration_manifest.json", manifest)
    return manifest


def create_demo_inputs(root: Path) -> tuple[list[str], list[str], list[str]]:
    root.mkdir(parents=True, exist_ok=True)
    x = np.linspace(200, 1800, 401)
    y = 100 + 20 * np.sin(x / 200) + 150 * np.exp(-0.5 * ((x - 850) / 35) ** 2)
    y[100] += 600
    spec = root / "spectre_acetaminophene_v1.csv"
    pd.DataFrame({"raman_shift": x, "intensity": y}).to_csv(spec, index=False)
    code = root / "old_raman_script.py"
    code.write_text("import numpy as np\n\ndef smooth_signal(y):\n    return np.convolve(y, np.ones(5)/5, mode='same')\n\ndef compute_auc(x, y):\n    return 1\n", encoding="utf-8")
    doc = root / "synergie_t3_notes.md"
    doc.write_text("# SYNERGIE-T3\nRaman AUC transition and HGFM mapping into DCT++ packets.\n", encoding="utf-8")
    return [str(spec)], [str(code)], [str(doc)]


def self_test() -> None:
    x = np.array([0, 1, 2, 3], dtype=float)
    y = np.array([0, 1, 1, 0], dtype=float)
    assert compute_auc(x, y)["auc"] > 0
    spike = np.ones(21)
    spike[10] = 100
    cleaned, count = remove_cosmic_spikes(spike, z_threshold=3)
    assert count >= 1 and cleaned[10] < 10
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        spectra, code, docs = create_demo_inputs(root / "inputs")
        args = argparse.Namespace(spectra=spectra, code=code, docs=docs, out=str(root / "out"))
        manifest = run_migration(args)
        assert Path(manifest["outputs"]["spectra"][0]["csv"]).exists()
        assert Path(manifest["outputs"]["code_inventory"]).exists()
        assert Path(manifest["outputs"]["docs"]["output"]).exists()
    print("[HGFM] self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="HGFM symbiotic migration runner")
    parser.add_argument("--spectra", nargs="*", help="CSV spectra globs")
    parser.add_argument("--code", nargs="*", help="Python file globs")
    parser.add_argument("--docs", nargs="*", help="Text/Markdown/LaTeX globs")
    parser.add_argument("--out", default="reports/hgfm_symbiotic_run")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.demo:
        demo_root = Path(args.out) / "demo_inputs"
        args.spectra, args.code, args.docs = create_demo_inputs(demo_root)
    manifest = run_migration(args)
    print(f"[HGFM] migration complete: {Path(args.out) / 'hgfm_migration_manifest.json'}")
    print(json.dumps(manifest["gates"], indent=2))


if __name__ == "__main__":
    main()
