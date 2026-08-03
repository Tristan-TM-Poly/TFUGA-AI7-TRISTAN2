from pathlib import Path

from omega_anime_animatic_t import build_eighth_fire_animatic_r2, compile_animatic_bundle


if __name__ == "__main__":
    output = Path("generated/omega_anime_animatic_t/eighth_fire_r2")
    timeline = build_eighth_fire_animatic_r2()
    manifest = compile_animatic_bundle(timeline, output)
    print(f"project={timeline.project_id}")
    print(f"scenes={len(timeline.scenes)} shots={len(timeline.shots)} duration={timeline.duration_s}")
    print(f"manifest={manifest['manifest_sha256']}")
    print(f"player={output / 'eighth-fire-animatic.html'}")
