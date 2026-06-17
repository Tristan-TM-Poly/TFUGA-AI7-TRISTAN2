"""Hexagonal CQC meta-operator seed.

Implements a lightweight roadmap version of:
    X_n = C_Pi o A o F_n^G o D

Families:
    F_3,3: hexagonal_crft x antenna
    F_3,8: hexagonal_crft x topological/nonreciprocal candidate

This is not a full-wave solver and not a proof of topology. It writes a CVCD
JSON report with separate radiative and topological OAK statuses.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CQCConfig:
    n_level: int = 3
    lattice_type: str = "hexagonal"
    stretch_x: float = 1.2
    stretch_y: float = 0.9
    cut_type: str = "zigzag"
    defect_strength: float = 0.0
    output_dir: str = "docs/cqc_runs"


@dataclass(frozen=True)
class OAKVerdict:
    radiative_status: str
    topological_status: str
    warnings: list[str]


class CQCMetaOperator:
    def __init__(self, config: CQCConfig):
        if config.n_level < 0:
            raise ValueError("n_level must be non-negative")
        if config.stretch_x <= 0 or config.stretch_y <= 0:
            raise ValueError("stretch values must be positive")
        if not 0.0 <= config.defect_strength <= 1.0:
            raise ValueError("defect_strength must be in [0, 1]")
        self.config = config
        self.n = config.n_level
        self.lattice = config.lattice_type
        self.point_group_initial = "C6v" if config.lattice_type == "hexagonal" else "Oh"
        self.point_group_final = self.point_group_initial
        self.a1 = np.array([1.0, 0.0], dtype=float)
        self.a2 = np.array([0.5, np.sqrt(3.0) / 2.0], dtype=float)
        self.stretch_tensor = np.eye(2)
        self.defect_field: dict[str, Any] = {"type": "none", "strength": 0.0}
        self.active_ports: list[str] = []
        self.g_sv_proxy = 0.0
        self.beta_1_proxy = 0
        self.eta_out = 0.0
        self.symmetry_break_ratio = 0.0
        self.candidate_edge_port = False
        self.oak = OAKVerdict("PENDING", "PENDING", [])

    def apply_defect_D(self) -> None:
        strength = self.config.defect_strength
        if strength > 0:
            self.defect_field = {
                "type": "controlled_hexagonal_mixer",
                "strength": round(strength, 4),
                "role": "localization and symmetry-mixing proxy",
            }
        print(f"[D] defect_field={self.defect_field}")

    def apply_fractal_equivariance_F(self) -> None:
        self.g_sv_proxy = float(3**self.n)
        self.beta_1_proxy = int(6 * (12 ** (self.n - 1))) if self.n > 0 else 0
        print(f"[F] beta_1_proxy={self.beta_1_proxy}; g_sv_proxy={self.g_sv_proxy:.3f}")

    def apply_stretch_A(self) -> None:
        sx = self.config.stretch_x
        sy = self.config.stretch_y
        self.stretch_tensor = np.array([[sx, 0.0], [0.0, sy]], dtype=float)
        self.a1 = self.stretch_tensor @ self.a1
        self.a2 = self.stretch_tensor @ self.a2
        self.symmetry_break_ratio = abs(sx - sy) / max(sx, sy)
        if self.symmetry_break_ratio > 1e-9:
            self.point_group_final = "C2v"
        anisotropy_gain = float(np.linalg.norm([sx, sy]) / np.sqrt(2.0))
        self.g_sv_proxy *= anisotropy_gain
        print(f"[A] stretch=({sx},{sy}); symmetry={self.point_group_final}")

    def apply_cut_port_C(self) -> None:
        cut_type = self.config.cut_type
        self.active_ports.append(cut_type)
        base_eta = {"zigzag": 0.85, "armchair": 0.62, "miller": 0.55, "random": 0.35}.get(cut_type, 0.40)
        defect_bonus = min(0.10, 0.20 * self.config.defect_strength)
        self.eta_out = min(0.95, base_eta + defect_bonus)
        self.candidate_edge_port = cut_type == "zigzag" and self.lattice == "hexagonal" and self.symmetry_break_ratio > 0.05
        print(f"[C] port={cut_type}; eta_out={self.eta_out:.3f}; candidate_edge_port={self.candidate_edge_port}")

    def run_oak_validation(self) -> OAKVerdict:
        warnings: list[str] = []
        if self.g_sv_proxy > 1000 and self.eta_out < 0.1:
            radiative = "REJECTED_DARK_MODE_RISK"
            warnings.append("high surface-volume proxy with poor extraction")
        elif self.beta_1_proxy > 0 and self.eta_out > 0.5:
            radiative = "VALIDATED_RADIATIVE_PROXY"
        else:
            radiative = "MARGINAL_NEEDS_FULL_WAVE"
            warnings.append("full-wave validation required")
        if self.candidate_edge_port:
            topo = "CANDIDATE_UNPROVEN_REQUIRES_INVARIANT"
            warnings.append("topological status is unproven: nu and gap are not computed")
        else:
            topo = "NOT_EVALUATED"
        self.oak = OAKVerdict(radiative, topo, warnings)
        print(f"[OAK] radiative={radiative}; topological={topo}")
        return self.oak

    def generate_cvcd(self) -> dict[str, Any]:
        cvcd = {
            "schema": "CVCD-CQC-RUN-v1",
            "families": ["F_3,3 hexagonal_crft x antenna", "F_3,8 hexagonal_crft x topological_candidate"],
            "operator_chain": "C_Pi o A o F_n^G o D",
            "lattice": self.lattice,
            "point_group_initial": self.point_group_initial,
            "point_group_final": self.point_group_final,
            "fractal_level_n": self.n,
            "stretch_tensor": np.round(self.stretch_tensor, 6).tolist(),
            "stretch_det": round(float(np.linalg.det(self.stretch_tensor)), 6),
            "symmetry_break_ratio": round(self.symmetry_break_ratio, 6),
            "defect_field": self.defect_field,
            "active_ports": self.active_ports,
            "hyper_loops_beta1_proxy": self.beta_1_proxy,
            "radiative_gain_g_sv_proxy": round(self.g_sv_proxy, 6),
            "extraction_eta_out": round(self.eta_out, 6),
            "candidate_edge_port": self.candidate_edge_port,
            "oak": asdict(self.oak),
        }
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"cvcd_hex_n{self.n}_{self.config.cut_type}.json"
        out_path.write_text(json.dumps(cvcd, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[CVCD] wrote {out_path}")
        return cvcd

    def run(self) -> dict[str, Any]:
        print("=== CQC HEX STRETCH ENGINE ===")
        self.apply_defect_D()
        self.apply_fractal_equivariance_F()
        self.apply_stretch_A()
        self.apply_cut_port_C()
        self.run_oak_validation()
        return self.generate_cvcd()


def parse_args() -> CQCConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-level", type=int, default=3)
    parser.add_argument("--lattice-type", default="hexagonal")
    parser.add_argument("--stretch-x", type=float, default=1.2)
    parser.add_argument("--stretch-y", type=float, default=0.9)
    parser.add_argument("--cut-type", default="zigzag", choices=["zigzag", "armchair", "miller", "random"])
    parser.add_argument("--defect-strength", type=float, default=0.0)
    parser.add_argument("--output-dir", default="docs/cqc_runs")
    args = parser.parse_args()
    return CQCConfig(**vars(args))


if __name__ == "__main__":
    CQCMetaOperator(parse_args()).run()
