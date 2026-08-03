from pathlib import Path

from omega_anime_season_t import build_eighth_fire_season_01_r4, compile_season_bundle


if __name__ == "__main__":
    output = Path("generated/omega_anime_season_t/season_01_r4")
    season = build_eighth_fire_season_01_r4()
    manifest = compile_season_bundle(season, output)
    print(f"season={season.season_id}")
    print(
        f"episodes={len(season.episodes)} duration_s={season.total_duration_s} "
        f"scenes={season.total_scenes} shots={season.total_shots}"
    )
    print(f"artifacts={manifest['artifact_count']}")
    print(f"manifest={manifest['manifest_sha256']}")
    print(f"dashboard={output / 'season-dashboard.html'}")
