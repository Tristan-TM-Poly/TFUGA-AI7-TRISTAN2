from __future__ import annotations

import hashlib
import html
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


class SpecError(ValueError):
    """Raised when a VisualSpec cannot support a truthful rendering."""


@dataclass(frozen=True)
class State:
    t_s: float
    displacement_m: float
    velocity_m_s: float

    def as_dict(self) -> dict[str, float]:
        return {
            "t_s": self.t_s,
            "displacement_m": self.displacement_m,
            "velocity_m_s": self.velocity_m_s,
        }


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_spec(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    required = {"visual", "model", "animation", "output", "oak"}
    missing = sorted(required - spec.keys())
    if missing:
        raise SpecError(f"missing sections: {', '.join(missing)}")
    if spec["model"].get("type") != "damped_harmonic_oscillator":
        raise SpecError("MVP supports model.type=damped_harmonic_oscillator")
    units = spec["model"].get("units", {})
    expected = {"mass": "kg", "stiffness": "N/m", "damping": "N*s/m", "displacement": "m"}
    if spec["oak"].get("require_units", True) and units != expected:
        raise SpecError(f"units must equal {expected}")
    frames = int(spec["animation"].get("frames", 0))
    if not 2 <= frames <= 10_000:
        raise SpecError("animation.frames must be between 2 and 10000")
    width = int(spec["output"].get("width", 0))
    height = int(spec["output"].get("height", 0))
    if not 64 <= width <= 4096 or not 64 <= height <= 4096:
        raise SpecError("output dimensions must be between 64 and 4096 pixels")
    duration = float(spec["animation"].get("duration_s", 0))
    fps = int(spec["animation"].get("fps", 0))
    if duration <= 0 or not 1 <= fps <= 120:
        raise SpecError("duration_s must be positive and fps must be between 1 and 120")
    return spec


def simulate(spec: dict[str, Any]) -> list[State]:
    p = spec["model"]["parameters"]
    mass = float(p["mass_kg"])
    stiffness = float(p["stiffness_n_m"])
    damping = float(p["damping_n_s_m"])
    x0 = float(p["initial_displacement_m"])
    v0 = float(p.get("initial_velocity_m_s", 0.0))
    if mass <= 0 or stiffness <= 0 or damping < 0:
        raise SpecError("mass and stiffness must be positive; damping must be non-negative")
    omega0 = math.sqrt(stiffness / mass)
    gamma = damping / (2 * mass)
    if gamma >= omega0:
        raise SpecError("MVP analytic solver supports the underdamped regime only")
    omega = math.sqrt(omega0 * omega0 - gamma * gamma)
    duration = float(spec["animation"]["duration_s"])
    count = int(spec["animation"]["frames"])
    states: list[State] = []
    coefficient = (v0 + gamma * x0) / omega
    for index in range(count):
        t = duration * index / (count - 1)
        envelope = math.exp(-gamma * t)
        c, s = math.cos(omega * t), math.sin(omega * t)
        x = envelope * (x0 * c + coefficient * s)
        v = envelope * (
            -gamma * (x0 * c + coefficient * s)
            + (-x0 * omega * s + coefficient * omega * c)
        )
        states.append(State(t, x, v))
    return states


def _geometry(spec: dict[str, Any], state: State) -> tuple[int, int, int, int]:
    width = int(spec["output"].get("width", 800))
    height = int(spec["output"].get("height", 450))
    amplitude = abs(float(spec["model"]["parameters"]["initial_displacement_m"])) or 1.0
    normalized = max(-1.2, min(1.2, state.displacement_m / amplitude))
    center_x = int(width * (0.55 + 0.25 * normalized))
    center_y = height // 2
    radius = max(12, min(width, height) // 14)
    return center_x, center_y, radius, width


def render_svg(spec: dict[str, Any], state: State) -> str:
    width, height = int(spec["output"]["width"]), int(spec["output"]["height"])
    x, y, r, _ = _geometry(spec, state)
    title = html.escape(str(spec["visual"]["title"]), quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#08111f"/>
<text x="24" y="36" fill="#e8f1ff" font-family="sans-serif" font-size="22">{title}</text>
<line x1="70" y1="{y}" x2="{x-r}" y2="{y}" stroke="#61dafb" stroke-width="5" stroke-dasharray="12 8"/>
<circle cx="{x}" cy="{y}" r="{r}" fill="#ffb000" stroke="#fff3c4" stroke-width="3"/>
<text x="24" y="{height-52}" fill="#a9bfd8" font-family="monospace" font-size="16">t = {state.t_s:.4f} s</text>
<text x="24" y="{height-26}" fill="#a9bfd8" font-family="monospace" font-size="16">x = {state.displacement_m:.6g} m</text>
<text x="{width-180}" y="{height-26}" fill="#73e2a7" font-family="sans-serif" font-size="14">OAK: SIMULATED</text>
</svg>'''


def render_frame(spec: dict[str, Any], state: State) -> Image.Image:
    width, height = int(spec["output"]["width"]), int(spec["output"]["height"])
    image = Image.new("RGB", (width, height), "#08111f")
    draw = ImageDraw.Draw(image)
    x, y, r, _ = _geometry(spec, state)
    draw.line((70, y, x - r, y), fill="#61dafb", width=5)
    draw.ellipse((x-r, y-r, x+r, y+r), fill="#ffb000", outline="#fff3c4", width=3)
    draw.text((24, 20), str(spec["visual"]["title"]), fill="#e8f1ff")
    draw.text((24, height-44), f"t={state.t_s:.4f} s   x={state.displacement_m:.6g} m", fill="#a9bfd8")
    draw.text((width-130, height-24), "OAK: SIMULATED", fill="#73e2a7")
    return image


def compile_visual(spec_path: Path, output_dir: Path) -> dict[str, Any]:
    spec = load_spec(spec_path)
    states = simulate(spec)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_payload = [state.as_dict() for state in states]
    (output_dir / "states.json").write_text(json.dumps(state_payload, indent=2), encoding="utf-8")
    (output_dir / "preview.svg").write_text(render_svg(spec, states[0]), encoding="utf-8")
    images = [render_frame(spec, state) for state in states]
    images[0].save(output_dir / "preview.png")
    fps = int(spec["animation"].get("fps", 24))
    images[0].save(
        output_dir / "animation.gif",
        save_all=True,
        append_images=images[1:],
        duration=max(1, round(1000 / fps)),
        loop=0,
        optimize=False,
    )
    artifact_names = ["states.json", "preview.svg", "preview.png", "animation.gif"]
    artifacts = {
        name: {"sha256": sha256_bytes((output_dir / name).read_bytes()), "bytes": (output_dir / name).stat().st_size}
        for name in artifact_names
    }
    manifest = {
        "schema_version": "1.0",
        "system": "OMEGA-VISUAL-SIM-T-infinity",
        "status": "SIMULATED",
        "spec_sha256": sha256_bytes(canonical_bytes(spec)),
        "model": spec["model"]["type"],
        "frames": len(states),
        "artifacts": artifacts,
        "known_limits": ["analytic underdamped oscillator", "schematic geometry not to scale"],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    oak = {
        "status": "PASS",
        "scientific_status": "SIMULATED",
        "checks": {
            "units_present": True,
            "deterministic_model": True,
            "provenance_hashes": True,
            "uncertainty_quantified": False,
            "experimentally_verified": False,
        },
        "residues": ["uncertainty model absent", "no experimental comparison"],
    }
    (output_dir / "oak_report.json").write_text(json.dumps(oak, indent=2), encoding="utf-8")
    return manifest


def verify_manifest(path: Path) -> list[str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for name, record in manifest.get("artifacts", {}).items():
        target = path.parent / name
        if not target.exists():
            errors.append(f"missing artifact: {name}")
        elif sha256_bytes(target.read_bytes()) != record["sha256"]:
            errors.append(f"hash mismatch: {name}")
    return errors
