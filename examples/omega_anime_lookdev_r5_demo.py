from pathlib import Path

from omega_anime_lookdev_t import build_eighth_fire_lookdev_r5, compile_lookdev_bundle


if __name__ == "__main__":
    output = Path("generated/omega_anime_lookdev_t/lookdev_r5")
    bible = build_eighth_fire_lookdev_r5()
    manifest = compile_lookdev_bundle(bible, output)
    print(f"style={bible.style_name}")
    print(f"characters={len(bible.characters)} episodes={len(bible.episodes)}")
    print(f"artifacts={manifest['artifact_count']} manifest={manifest['manifest_sha256']}")
