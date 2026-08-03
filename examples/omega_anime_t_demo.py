"""Compile the canonical Ω-ANIME-T∞ R0.1 evidence bundle."""

from pathlib import Path

from omega_anime_t import build_eighth_fire_project, compile_project_bundle


if __name__ == "__main__":
    destination = Path("generated/omega_anime_t/eighth_fire_r0_1")
    manifest = compile_project_bundle(build_eighth_fire_project(), destination)
    print(f"Wrote {manifest['project_id']} to {destination}")
    print(f"OAK decision: {manifest['decision']}")
    print(f"Manifest SHA-256: {manifest['manifest_sha256']}")
