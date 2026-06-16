#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Science Domain Omni Harvester

Broad offline tensor atlas for important scientific domains.

Purpose
-------
Generate deterministic synthetic/benchmark-like tensors for many science domains,
then submit every tensor to JKD -> FFWT/CVCD -> OAK. This extends Accumulation
Pure beyond a few axes without claiming that synthetic tensors are real empirical
validation.

Design locks
------------
- offline by default
- stdlib + numpy only
- no external APIs, no deployment, no publication
- writes only reports/jkd/science_domain_omni_report.json
- every domain is a candidate signal, not a scientific proof
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Tuple
import argparse
import json
import math
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from jkd_fusion_strike import jkd_strike  # noqa: E402

REPORT_PATH = ROOT / "reports" / "jkd" / "science_domain_omni_report.json"
DEFAULT_LENGTH = 512


def utc_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rng_for(domain: str) -> np.random.Generator:
    seed = abs(hash((domain, "TTM-SCIENCE-OMNI"))) % (2**32)
    return np.random.default_rng(seed)


def normalize(x: np.ndarray, n: int = DEFAULT_LENGTH) -> np.ndarray:
    arr = np.asarray(x, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        arr = np.zeros(n)
    if arr.size != n:
        if arr.size == 1:
            arr = np.full(n, float(arr[0]))
        else:
            src = np.linspace(0.0, 1.0, arr.size)
            dst = np.linspace(0.0, 1.0, n)
            arr = np.interp(dst, src, arr)
    return arr


def wave_mix(domain: str, freqs: Tuple[float, ...], noise: float = 0.05, n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for(domain)
    t = np.linspace(0.0, 2.0 * math.pi, n)
    y = np.zeros(n)
    for idx, freq in enumerate(freqs, start=1):
        y += (1.0 / idx) * np.sin(freq * t + 0.37 * idx)
    y += rng.normal(0.0, noise, n)
    return y


def pulse_train(domain: str, centers: Tuple[float, ...], widths: Tuple[float, ...], n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for(domain)
    x = np.linspace(0.0, 1.0, n)
    y = rng.normal(0.0, 0.02, n)
    for c, w in zip(centers, widths):
        y += np.exp(-((x - c) ** 2) / (2.0 * w * w))
    return y


def diffusion_profile(domain: str, d: float = 0.12, n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for(domain)
    x = np.linspace(-4.0, 4.0, n)
    y = np.exp(-(x**2) / (4.0 * d)) / math.sqrt(max(4.0 * math.pi * d, 1e-12))
    return y + rng.normal(0.0, 0.01, n)


def chaotic_map(domain: str, r: float = 3.85, n: int = DEFAULT_LENGTH) -> np.ndarray:
    x = np.empty(n)
    x[0] = 0.271828
    for i in range(1, n):
        x[i] = r * x[i - 1] * (1.0 - x[i - 1])
    return x


def random_field_projection(domain: str, n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for(domain)
    mat = rng.normal(0.0, 1.0, (32, 32))
    # deterministic smooth kernel through cumulative averaging
    smooth = np.cumsum(np.cumsum(mat, axis=0), axis=1)
    smooth = smooth / (np.max(np.abs(smooth)) + 1e-12)
    return normalize(smooth.reshape(-1), n)


def network_burst(domain: str, n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for(domain)
    y = rng.poisson(12, n).astype(float)
    for center, amp in [(128, 80), (256, 160), (384, 60)]:
        width = 30
        x = np.linspace(-3, 3, width)
        y[center:center + width] += amp * np.exp(-(x**2))
    return y


def domain_generators() -> Dict[str, Tuple[str, Callable[[], np.ndarray]]]:
    return {
        # Mathematical / formal sciences
        "mathematics_number_theory": ("formal", lambda: np.asarray([((i * i + 3 * i + 7) % 97) for i in range(DEFAULT_LENGTH)], dtype=float)),
        "mathematics_dynamical_systems": ("formal", lambda: chaotic_map("mathematics_dynamical_systems", 3.91)),
        "statistics_probability": ("formal", lambda: np.cumsum(rng_for("statistics_probability").normal(0, 1, DEFAULT_LENGTH))),
        "computer_science_algorithms": ("formal", lambda: np.asarray([math.log2(i + 2) * ((i % 7) + 1) for i in range(DEFAULT_LENGTH)], dtype=float)),
        "information_theory": ("formal", lambda: wave_mix("information_theory", (1, 2, 4, 8, 16), 0.03)),
        "systems_control": ("formal", lambda: np.exp(-np.linspace(0, 8, DEFAULT_LENGTH)) * np.cos(7 * np.linspace(0, 8, DEFAULT_LENGTH))),

        # Physical sciences
        "physics_mechanics": ("physical", lambda: wave_mix("physics_mechanics", (1.0, 2.0, 3.0), 0.02)),
        "physics_quantum": ("physical", lambda: np.abs(wave_mix("physics_quantum", (2, 5, 11), 0.01)) ** 2),
        "physics_relativity": ("physical", lambda: 1.0 / np.sqrt(1.0 + np.linspace(0.0, 8.0, DEFAULT_LENGTH) ** 2)),
        "chemistry_spectroscopy": ("physical", lambda: pulse_train("chemistry_spectroscopy", (0.18, 0.52, 0.76), (0.012, 0.025, 0.018))),
        "materials_crystals": ("physical", lambda: wave_mix("materials_crystals", (4, 8, 12, 16), 0.015) + pulse_train("materials_crystals_peaks", (0.25, 0.5, 0.75), (0.01, 0.01, 0.01))),
        "astronomy_lightcurve": ("physical", lambda: wave_mix("astronomy_lightcurve", (1.0, 1.03, 7.0), 0.04)),
        "earth_geophysics": ("earth", lambda: wave_mix("earth_geophysics", (0.5, 3.2, 13.0), 0.08)),
        "climate_atmosphere": ("earth", lambda: wave_mix("climate_atmosphere", (1.0, 2.0, 6.0, 19.0), 0.12)),
        "oceanography": ("earth", lambda: wave_mix("oceanography", (0.25, 1.0, 2.2), 0.06)),
        "hydrology": ("earth", lambda: diffusion_profile("hydrology", 0.18) + 0.1 * wave_mix("hydrology_wave", (3, 9), 0.02)),

        # Life and medical sciences
        "biology_genomics": ("life", lambda: np.tile([1, 3, 2, 4, 1, 4, 3, 2], DEFAULT_LENGTH // 8 + 1)[:DEFAULT_LENGTH]),
        "biology_ecology": ("life", lambda: chaotic_map("biology_ecology", 3.62) + 0.1 * wave_mix("biology_ecology_wave", (2, 5), 0.02)),
        "neuroscience_eeg": ("life", lambda: wave_mix("neuroscience_eeg", (2, 6, 10, 20, 40), 0.10)),
        "medicine_vitals": ("life", lambda: wave_mix("medicine_vitals", (1.2, 9.0), 0.05) + pulse_train("medicine_vitals_pulse", (0.2, 0.4, 0.6, 0.8), (0.01, 0.01, 0.01, 0.01))),
        "pharmacology_response": ("life", lambda: 1.0 - np.exp(-np.linspace(0, 7, DEFAULT_LENGTH)) + rng_for("pharmacology_response").normal(0, 0.03, DEFAULT_LENGTH)),
        "epidemiology_curve": ("life", lambda: 1.0 / (1.0 + np.exp(-8.0 * (np.linspace(0, 1, DEFAULT_LENGTH) - 0.45)))),

        # Cognitive, social, and economic sciences
        "psychology_reaction": ("cognitive_social", lambda: rng_for("psychology_reaction").lognormal(mean=0.0, sigma=0.35, size=DEFAULT_LENGTH)),
        "linguistics_signal": ("cognitive_social", lambda: np.asarray([ord(ch) for ch in (("syntax semantics phonology morphology pragmatics ") * 20)[:DEFAULT_LENGTH]], dtype=float)),
        "economics_cycles": ("cognitive_social", lambda: wave_mix("economics_cycles", (0.7, 3.0, 9.0), 0.12) + np.linspace(0, 1, DEFAULT_LENGTH)),
        "sociology_networks": ("cognitive_social", lambda: network_burst("sociology_networks")),
        "education_learning": ("cognitive_social", lambda: np.log1p(np.linspace(0, 20, DEFAULT_LENGTH)) + rng_for("education_learning").normal(0, 0.06, DEFAULT_LENGTH)),

        # Engineering and applied sciences
        "electrical_rlc": ("engineering", lambda: np.exp(-0.25 * np.linspace(0, 12, DEFAULT_LENGTH)) * np.cos(6.0 * np.linspace(0, 12, DEFAULT_LENGTH))),
        "mechanical_vibration": ("engineering", lambda: wave_mix("mechanical_vibration", (5, 5.4, 16), 0.06)),
        "civil_structural": ("engineering", lambda: pulse_train("civil_structural", (0.25, 0.5, 0.72), (0.04, 0.03, 0.05))),
        "robotics_trajectory": ("engineering", lambda: np.sin(np.linspace(0, 8, DEFAULT_LENGTH)) + 0.3 * np.sign(np.sin(np.linspace(0, 40, DEFAULT_LENGTH)))),
        "cybersecurity_traffic": ("engineering", lambda: network_burst("cybersecurity_traffic")),
        "ai_embedding_geometry": ("engineering", lambda: random_field_projection("ai_embedding_geometry")),
    }


def compact_strike(tensor: np.ndarray, permutation_checks: int) -> Dict[str, Any]:
    result = jkd_strike(tensor, permutation_checks=permutation_checks)
    signatures = result.get("signatures_cvcd", {})
    control = result.get("permutation_control", {})
    return {
        "verdict": result.get("verdict"),
        "oak_score": result.get("oak_score"),
        "shape": result.get("shape"),
        "flattened_size": result.get("flattened_size"),
        "selected_invariants": {
            "fractal_ratio": signatures.get("fractal_ratio"),
            "ffwt_energy_entropy": signatures.get("ffwt_energy_entropy"),
            "ffwt_mean_adjacent_coherence": signatures.get("ffwt_mean_adjacent_coherence"),
            "ffwt_dominant_level": signatures.get("ffwt_dominant_level"),
            "ffwt_dominant_relative_energy": signatures.get("ffwt_dominant_relative_energy"),
            "null_z_score": control.get("null_z_score"),
            "null_percentile": control.get("null_percentile"),
            "used_permutations": control.get("used_permutations"),
        },
    }


def load_history() -> Dict[str, Any]:
    if not REPORT_PATH.exists():
        return {"system": "TTM Science Domain Omni Harvester", "runs": []}
    try:
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "runs" in data:
            return data
    except Exception:
        pass
    return {"system": "TTM Science Domain Omni Harvester", "runs": []}


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Harvest synthetic tensors across important science domains")
    parser.add_argument("--permutation-checks", type=int, default=8)
    args = parser.parse_args(argv)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    run: Dict[str, Any] = {
        "timestamp": utc_stamp(),
        "permutation_checks": int(args.permutation_checks),
        "domain_count": 0,
        "domains": {},
    }

    for name, (family, generator) in domain_generators().items():
        tensor = normalize(generator())
        run["domains"][name] = {
            "family": family,
            "source": "offline:synthetic_science_tensor",
            "strike": compact_strike(tensor, args.permutation_checks),
        }
    run["domain_count"] = len(run["domains"])

    history = load_history()
    history.setdefault("runs", []).append(run)
    history["last_run"] = run
    REPORT_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"domain_count": run["domain_count"], "families": sorted({v["family"] for v in run["domains"].values()})}, indent=2, ensure_ascii=False))
    return run


if __name__ == "__main__":
    main()
