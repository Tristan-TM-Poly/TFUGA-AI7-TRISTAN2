#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Omni Tensor Harvester

Silent-accumulation prototype for diversified JKD/OAK sampling.

Axes
----
- finance: public BTC hourly candles when available, deterministic fallback.
- weather: public wind-speed forecast/history when available, deterministic fallback.
- nlp: public Wikipedia random-title sample when available, deterministic fallback.
- biology: deterministic synthetic nucleotide signal with structured gene motif.
- cyber: deterministic synthetic traffic signal with DDoS-like anomaly.

Design locks
------------
- Python stdlib + numpy only.
- No keys, no writes outside reports/jkd/.
- API failures fall back to deterministic synthetic tensors.
- Reports are append-only by timestamp.
- This is not financial, medical, cybersecurity, or climate advice; it is an OAK
  signal-processing accumulation harness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Tuple
import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from jkd_fusion_strike import jkd_strike  # noqa: E402

REPORT_PATH = ROOT / "reports" / "jkd" / "omni_harvester_report.json"
DEFAULT_LENGTH = 512


def utc_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rng_for(axis: str) -> np.random.Generator:
    seed = abs(hash((axis, "TTM-OMNI-HARVESTER"))) % (2**32)
    return np.random.default_rng(seed)


def fetch_json(url: str, timeout: int = 10) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "TTM-OmniTensorHarvester/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def resample_1d(values: np.ndarray, n: int = DEFAULT_LENGTH) -> np.ndarray:
    x = np.asarray(values, dtype=float).reshape(-1)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return np.zeros(n, dtype=float)
    if x.size == n:
        return x
    if x.size == 1:
        return np.full(n, float(x[0]))
    source = np.linspace(0.0, 1.0, x.size)
    target = np.linspace(0.0, 1.0, n)
    return np.interp(target, source, x)


def fallback_finance(n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for("finance")
    returns = rng.normal(0.0, 0.018, n)
    returns[260:285] += np.linspace(-0.02, 0.015, 25)
    return 100.0 * np.cumprod(1.0 + returns)


def fallback_weather(n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for("weather")
    x = np.linspace(0.0, 16.0 * math.pi, n)
    return 12.0 + 2.0 * np.sin(x / 2.0) + 1.1 * np.sin(2.7 * x + 0.4) + rng.normal(0.0, 0.35, n)


def fallback_nlp(n: int = DEFAULT_LENGTH) -> np.ndarray:
    text = (
        "TFUGA HGFM CVCD OAK SAGE JKD FFWT tensorial invariant compression "
        "negative memory canon fertile residue analytic signal physics "
    )
    repeated = (text * ((n // len(text)) + 2))[:n]
    return np.asarray([ord(ch) for ch in repeated], dtype=float)


def fallback_biology(n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for("biology")
    junk = rng.choice([1.0, 2.0, 3.0, 4.0], n)
    motif = np.tile([1.0, 3.0, 2.0, 4.0, 1.0, 4.0, 3.0, 2.0], 24)
    start = n // 3
    end = min(n, start + motif.size)
    junk[start:end] = motif[: end - start]
    return junk


def fallback_cyber(n: int = DEFAULT_LENGTH) -> np.ndarray:
    rng = rng_for("cyber")
    traffic = rng.poisson(lam=15, size=n).astype(float)
    width = min(64, n // 5)
    center = n // 2
    x = np.linspace(-4.0, 4.0, width)
    spike = np.exp(-(x**2)) * 180.0
    traffic[center : center + width] += spike
    return traffic


def harvest_finance(live: bool) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    if live:
        try:
            data = fetch_json("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=512")
            closes = np.asarray([float(row[4]) for row in data], dtype=float)
            return resample_1d(closes), "live:binance_btcusdt_1h", {"samples": int(closes.size)}
        except Exception as exc:
            return fallback_finance(), "fallback:geometric_walk", {"error": str(exc)[:500]}
    return fallback_finance(), "offline:fallback_finance", {}


def harvest_weather(live: bool) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    if live:
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                "latitude=45.5017&longitude=-73.5673&hourly=wind_speed_10m&past_days=7&forecast_days=1"
            )
            data = fetch_json(url)
            wind = np.asarray(data["hourly"]["wind_speed_10m"], dtype=float)
            return resample_1d(np.nan_to_num(wind, nan=float(np.nanmean(wind)))), "live:open_meteo_montreal_wind", {"samples": int(wind.size)}
        except Exception as exc:
            return fallback_weather(), "fallback:synthetic_wind", {"error": str(exc)[:500]}
    return fallback_weather(), "offline:fallback_weather", {}


def harvest_nlp(live: bool) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    if live:
        try:
            url = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=random&rnnamespace=0&rnlimit=1"
            data = fetch_json(url)
            title = str(data["query"]["random"][0]["title"])
            repeated = (title + " ") * ((DEFAULT_LENGTH // (len(title) + 1)) + 2)
            tensor = np.asarray([ord(ch) for ch in repeated[:DEFAULT_LENGTH]], dtype=float)
            return tensor, "live:wikipedia_random_title", {"title": title}
        except Exception as exc:
            return fallback_nlp(), "fallback:synthetic_semantic", {"error": str(exc)[:500]}
    return fallback_nlp(), "offline:fallback_nlp", {}


def harvest_biology(live: bool) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    return fallback_biology(), "synthetic:nucleotide_motif", {"mapping": "A=1,C=2,G=3,T=4"}


def harvest_cyber(live: bool) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    return fallback_cyber(), "synthetic:traffic_with_anomaly", {"units": "requests_per_second_like"}


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
        return {"system": "TTM Omni Tensor Harvester", "runs": []}
    try:
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "runs" in data:
            return data
        # Backward-compatible migration from timestamp-root dict.
        return {"system": "TTM Omni Tensor Harvester", "runs": [{"timestamp": k, "axes": v} for k, v in data.items()]}
    except Exception:
        return {"system": "TTM Omni Tensor Harvester", "runs": []}


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Omni Tensor Harvester for silent JKD/OAK accumulation")
    parser.add_argument("--live", action="store_true", help="try public endpoints before deterministic fallback")
    parser.add_argument("--permutation-checks", type=int, default=16, help="requested JKD permutation checks")
    args = parser.parse_args(argv)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    axes: Dict[str, Callable[[bool], Tuple[np.ndarray, str, Dict[str, Any]]]] = {
        "finance_btc": harvest_finance,
        "weather_wind": harvest_weather,
        "nlp_wikipedia": harvest_nlp,
        "biology_dna": harvest_biology,
        "cyber_traffic": harvest_cyber,
    }

    run: Dict[str, Any] = {
        "timestamp": utc_stamp(),
        "live_requested": bool(args.live),
        "permutation_checks": int(args.permutation_checks),
        "axes": {},
    }

    for name, func in axes.items():
        tensor, source, meta = func(args.live)
        strike = compact_strike(tensor, permutation_checks=args.permutation_checks)
        run["axes"][name] = {"source": source, "metadata": meta, "strike": strike}

    history = load_history()
    history.setdefault("runs", []).append(run)
    history["last_run"] = run
    REPORT_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(run, indent=2, ensure_ascii=False, sort_keys=True))
    return run


if __name__ == "__main__":
    main()
