#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: OMEGA-MAX PROTOTYPE BENCHMARK

Pipeline canonique:
Signal -> FFWT fractal core -> HAC/CVCD invariants -> equation parameter -> OAK -> Canon / M_MINUS

Benchmarks inclus:
B1: oscillateur amorti       x(t)=A exp(-gamma t) cos(w0 t + phi) + noise
B2: RLC sous-amorti          q(t)=A exp(-alpha t) cos(wd t + phi) + noise
B3: diffusion 1D             u(x,t)=Gaussian variance 2Dt + noise

Dépendances: numpy seulement.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import math
import sys
import time

import numpy as np

# Import du vrai noyau FFWT gardé dans core/.
REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from omega_ffwt_core import extract_ffwt_signatures, haar_fractal_transform  # noqa: E402


# ==============================================================================
# Configuration
# ==============================================================================

RNG = np.random.default_rng(42)
REPORT_PATH = Path("omega_max_oak_report.json")


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark: str
    relation_type: str
    extracted: Dict[str, float]
    ground_truth: Dict[str, float]
    errors: Dict[str, float]
    oak_score: float
    verdict: str
    notes: str


# ==============================================================================
# 1. Génération des signaux
# ==============================================================================

def get_b1_damped_oscillator(t: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
    """B1: oscillateur amorti libre."""
    gamma = 0.50
    w0 = 5.00
    phi = 0.20
    signal = np.exp(-gamma * t) * np.cos(w0 * t + phi)
    noise = RNG.normal(0.0, 0.035, size=t.size)
    return signal + noise, {"gamma_true": gamma, "w0_true": w0, "phi_true": phi}


def get_b2_rlc_underdamped(t: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
    """B2: réponse libre d'un RLC série sous-amorti.

    Équation: L q'' + R q' + (1/C) q = 0
    alpha = R/(2L), omega0 = 1/sqrt(LC), wd = sqrt(omega0^2 - alpha^2)
    """
    L = 1.0
    C = 0.04
    R = 0.70
    alpha = R / (2.0 * L)
    omega0 = 1.0 / math.sqrt(L * C)
    wd = math.sqrt(max(omega0 * omega0 - alpha * alpha, 0.0))
    phi = -0.15
    q = np.exp(-alpha * t) * np.cos(wd * t + phi)
    noise = RNG.normal(0.0, 0.030, size=t.size)
    truth = {
        "L_true": L,
        "C_true": C,
        "R_true": R,
        "alpha_true": alpha,
        "wd_true": wd,
        "omega0_true": omega0,
        "Q_true": omega0 / (2.0 * alpha),
    }
    return q + noise, truth


def get_b3_diffusion_profile(x: np.ndarray, t_obs: float) -> Tuple[np.ndarray, Dict[str, float]]:
    """B3: profil spatial d'une diffusion 1D à temps fixé.

    Solution fondamentale normalisée:
    u(x,t)=1/sqrt(4*pi*D*t) exp(-x^2/(4Dt))
    Var[x]=2Dt.
    """
    D = 1.50
    clean = (1.0 / np.sqrt(4.0 * np.pi * D * t_obs)) * np.exp(-(x**2) / (4.0 * D * t_obs))
    noise = RNG.normal(0.0, 0.0025, size=x.size)
    return clean + noise, {"D_true": D, "t_obs": t_obs}


# ==============================================================================
# 2. Microscope FFWT/HAC/CVCD
# ==============================================================================

def compute_ffwt_cvcd_signature(signal: np.ndarray, max_levels: int = 8) -> Dict[str, float]:
    """Transforme le signal en signatures FFWT-CVCD réelles et OAK-safe."""
    coeffs = haar_fractal_transform(signal, max_levels=max_levels, adaptive=True)
    return extract_ffwt_signatures(coeffs)


def analytic_signal_numpy(signal: np.ndarray) -> np.ndarray:
    """Signal analytique façon Hilbert, implémenté uniquement avec numpy."""
    n = signal.size
    spectrum = np.fft.fft(signal)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(spectrum * h)


def parabolic_fft_peak(freqs: np.ndarray, power: np.ndarray, idx: int) -> float:
    """Interpolation parabolique locale du pic FFT."""
    if idx <= 0 or idx >= len(power) - 1:
        return float(freqs[idx])
    y0, y1, y2 = np.log(power[idx - 1: idx + 2] + 1e-30)
    denom = y0 - 2.0 * y1 + y2
    if abs(denom) < 1e-18:
        return float(freqs[idx])
    delta = 0.5 * (y0 - y2) / denom
    df = freqs[1] - freqs[0]
    return float(freqs[idx] + delta * df)


def estimate_damped_mode(t: np.ndarray, signal: np.ndarray) -> Dict[str, float]:
    """Extrait gamma et omega dominant d'un signal oscillant amorti.

    Le noyau FFWT fournit les signatures multi-échelles ; l'estimateur physique
    garde la précision OAK par enveloppe analytique + FFT/phase fusion.
    """
    centered = signal - np.mean(signal)
    dt = float(np.median(np.diff(t)))
    ffwt = compute_ffwt_cvcd_signature(centered)

    # Fréquence dominante par FFT fenêtrée, avec garde-fou anti-bruit HF.
    window = np.hanning(centered.size)
    spectrum = np.fft.rfft(centered * window)
    freqs_hz = np.fft.rfftfreq(centered.size, d=dt)
    power = np.abs(spectrum) ** 2
    physical_band = (freqs_hz >= 0.05) & (freqs_hz <= 3.0)
    if not np.any(physical_band):
        raise ValueError("no frequency bins in physical band")
    band_indices = np.flatnonzero(physical_band)
    idx = int(band_indices[np.argmax(power[physical_band])])
    f_peak = parabolic_fft_peak(freqs_hz, power, idx)
    omega_eff = 2.0 * np.pi * f_peak

    # Gamma par enveloppe analytique robuste.
    analytic = analytic_signal_numpy(centered)
    envelope = np.abs(analytic)
    noise_floor = float(np.median(envelope[int(0.85 * envelope.size):]))
    envelope_clean = np.clip(envelope - 0.75 * noise_floor, 1e-12, None)
    mask = envelope_clean > max(2.25 * noise_floor, np.percentile(envelope_clean, 55))
    edge = max(5, centered.size // 50)
    mask[:edge] = False
    mask[-edge:] = False
    if int(np.sum(mask)) < 20:
        mask = np.zeros_like(envelope_clean, dtype=bool)
        mask[edge:int(0.45 * envelope_clean.size)] = True
    slope, _ = np.polyfit(t[mask], np.log(envelope_clean[mask]), 1)
    gamma_eff = max(0.0, float(-slope))

    phase = np.unwrap(np.angle(analytic))
    phase_slope, _ = np.polyfit(t[mask], phase[mask], 1)
    omega_phase_eff = abs(float(phase_slope))
    omega_fused = 0.85 * omega_eff + 0.15 * omega_phase_eff

    # FFWT physical hints: dominant dyadic level and coherence are kept as
    # explanatory CVCD features, not as the sole source of the parameter estimate.
    return {
        "gamma_eff": gamma_eff,
        "omega_eff": omega_fused,
        "omega_fft_eff": omega_eff,
        "omega_phase_eff": omega_phase_eff,
        "envelope_points": float(np.sum(mask)),
        "noise_floor_eff": noise_floor,
        **ffwt,
    }


def estimate_diffusion_constant(x: np.ndarray, profile: np.ndarray, t_obs: float) -> Dict[str, float]:
    """Estime D via la pente log-gaussienne et ajoute les signatures FFWT.

    Pour la solution fondamentale, log u = const - x^2/(4Dt). La pente centrale
    est plus robuste au bruit de queue que la variance brute. Les ratios FFWT
    sont conservés comme invariants multi-échelles de l'étalement.
    """
    y = np.asarray(profile, dtype=float)
    ffwt = compute_ffwt_cvcd_signature(y)

    baseline = float(np.percentile(y, 3))
    y_clean = np.clip(y - baseline, 1e-12, None)
    central = y_clean > (0.12 * float(np.max(y_clean)))
    if int(np.sum(central)) < 20:
        raise ValueError("not enough central diffusion samples for log-gaussian fit")
    slope, _ = np.polyfit(x[central] ** 2, np.log(y_clean[central]), 1)
    D_log = -1.0 / (4.0 * t_obs * slope) if slope < 0 else float("inf")

    weights = y_clean * central
    weights = weights / np.sum(weights)
    mean_x = float(np.sum(weights * x))
    var_x = float(np.sum(weights * (x - mean_x) ** 2))
    D_var = var_x / (2.0 * t_obs)

    # FFWT-derived surrogate reading of diffusion. This is intentionally not used
    # as the primary D yet; it becomes an OAK-tracked candidate invariant.
    D_ffwt_candidate = float(ffwt.get("fractal_ratio", 0.0) * (t_obs / math.pi))

    return {
        "D_eff": float(D_log),
        "D_var_control": float(D_var),
        "D_ffwt_candidate": D_ffwt_candidate,
        "mean_x_eff": mean_x,
        "var_x_eff": var_x,
        **ffwt,
    }


# ==============================================================================
# 3. Tribunal OAK
# ==============================================================================

def relative_error(estimate: float, truth: float, eps: float = 1e-12) -> float:
    return abs(float(estimate) - float(truth)) / (abs(float(truth)) + eps)


def oak_score_from_errors(errors: Dict[str, float], complexity_penalty: float) -> float:
    """Score OAK compact : 100 si erreur nulle, pénalisé par erreur et complexité."""
    if not errors:
        return 0.0
    weighted_error = float(np.mean(list(errors.values())))
    score = 100.0 * max(0.0, 1.0 - weighted_error) - complexity_penalty
    return float(np.clip(score, 0.0, 100.0))


def oak_verdict(score: float, canon_threshold: float = 80.0, fertile_threshold: float = 55.0) -> str:
    if score >= canon_threshold:
        return "CANON"
    if score >= fertile_threshold:
        return "FERTILE"
    return "M_MINUS"


def run_b1(t: np.ndarray) -> BenchmarkResult:
    signal, truth = get_b1_damped_oscillator(t)
    inv = estimate_damped_mode(t, signal)
    extracted = {
        "gamma_eff": inv["gamma_eff"],
        "w0_eff": inv["omega_eff"],
        "ffwt_dominant_level": inv["ffwt_dominant_level"],
        "ffwt_energy_entropy": inv["ffwt_energy_entropy"],
        "ffwt_mean_adjacent_coherence": inv["ffwt_mean_adjacent_coherence"],
        "fractal_ratio": inv["fractal_ratio"],
    }
    errors = {
        "gamma_rel_error": relative_error(extracted["gamma_eff"], truth["gamma_true"]),
        "w0_rel_error": relative_error(extracted["w0_eff"], truth["w0_true"]),
    }
    score = oak_score_from_errors(errors, complexity_penalty=5.0)
    return BenchmarkResult(
        "B1",
        "Damped oscillator",
        extracted,
        truth,
        errors,
        score,
        oak_verdict(score),
        "gamma/w0 extracted with robust physics estimator; FFWT signatures attached as CVCD evidence",
    )


def run_b2(t: np.ndarray) -> BenchmarkResult:
    signal, truth = get_b2_rlc_underdamped(t)
    inv = estimate_damped_mode(t, signal)
    alpha_eff = inv["gamma_eff"]
    wd_eff = inv["omega_eff"]
    omega0_eff = math.sqrt(max(wd_eff * wd_eff + alpha_eff * alpha_eff, 0.0))
    Q_eff = omega0_eff / max(2.0 * alpha_eff, 1e-12)
    extracted = {
        "alpha_eff": alpha_eff,
        "wd_eff": wd_eff,
        "omega0_eff": omega0_eff,
        "Q_eff": Q_eff,
        "ffwt_dominant_level": inv["ffwt_dominant_level"],
        "ffwt_energy_entropy": inv["ffwt_energy_entropy"],
        "ffwt_mean_adjacent_coherence": inv["ffwt_mean_adjacent_coherence"],
        "fractal_ratio": inv["fractal_ratio"],
    }
    errors = {
        "alpha_rel_error": relative_error(alpha_eff, truth["alpha_true"]),
        "wd_rel_error": relative_error(wd_eff, truth["wd_true"]),
        "omega0_rel_error": relative_error(omega0_eff, truth["omega0_true"]),
        "Q_rel_error": relative_error(Q_eff, truth["Q_true"]),
    }
    score = oak_score_from_errors(errors, complexity_penalty=7.5)
    return BenchmarkResult(
        "B2",
        "RLC underdamped",
        extracted,
        truth,
        errors,
        score,
        oak_verdict(score),
        "RLC parameters inferred from damped mode; FFWT multiscale evidence included",
    )


def run_b3(x: np.ndarray, t_obs: float) -> BenchmarkResult:
    profile, truth = get_b3_diffusion_profile(x, t_obs)
    extracted = estimate_diffusion_constant(x, profile, t_obs)
    errors = {"D_rel_error": relative_error(extracted["D_eff"], truth["D_true"])}
    # D_ffwt_candidate is not yet canonical; track it in report, but score the
    # physical D estimator until OAK validates a pure FFWT diffusion map.
    errors["D_ffwt_candidate_rel_error"] = relative_error(extracted["D_ffwt_candidate"], truth["D_true"])
    score = oak_score_from_errors({"D_rel_error": errors["D_rel_error"]}, complexity_penalty=4.0)
    return BenchmarkResult(
        "B3",
        "Diffusion 1D",
        extracted,
        truth,
        errors,
        score,
        oak_verdict(score),
        "D extracted from log-gaussian physics; FFWT fractal_ratio tracked as candidate diffusion invariant",
    )


# ==============================================================================
# 4. Exécution canonique
# ==============================================================================

def main() -> Dict[str, Any]:
    start = time.time()
    print("=== [IGNITION] OMEGA-FFWT-HAC-CVCD-ASP-MAX :: FFWT CORE BENCHMARK B1-B3 ===")

    t = np.linspace(0.0, 12.0, 2400)
    x = np.linspace(-12.0, 12.0, 2400)
    t_diff = 2.0

    results = [run_b1(t), run_b2(t), run_b3(x, t_diff)]
    canon: List[Dict[str, Any]] = []
    m_minus: List[Dict[str, Any]] = []
    fertile: List[Dict[str, Any]] = []

    for result in results:
        payload = asdict(result)
        print(f"\n--- {result.benchmark}: {result.relation_type} ---")
        print("extracted:", json.dumps(result.extracted, indent=2, sort_keys=True))
        print("truth:    ", json.dumps(result.ground_truth, indent=2, sort_keys=True))
        print("errors:   ", json.dumps(result.errors, indent=2, sort_keys=True))
        print(f"OAK score: {result.oak_score:.2f} -> {result.verdict}")
        if result.verdict == "CANON":
            canon.append(payload)
        elif result.verdict == "FERTILE":
            fertile.append(payload)
        else:
            m_minus.append(payload)

    report = {
        "system": "OMEGA-FFWT-HAC-CVCD-ASP-MAX",
        "pipeline": "Signal -> FFWT fractal core -> HAC/CVCD invariants -> Equation parameter -> OAK -> Canon/M_MINUS",
        "created_at_unix": time.time(),
        "runtime_seconds": time.time() - start,
        "canon": canon,
        "fertile": fertile,
        "M_MINUS": m_minus,
        "results": [asdict(r) for r in results],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[REPORT] {REPORT_PATH.resolve()}")
    print("=== [END] OAK registry updated locally. ===")
    return report


if __name__ == "__main__":
    main()
