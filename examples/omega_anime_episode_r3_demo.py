from pathlib import Path

from omega_anime_episode_t import build_eighth_fire_episode_01_r3, compile_episode_bundle


if __name__ == "__main__":
    output = Path("generated/omega_anime_episode_t/episode_01_r3")
    episode = build_eighth_fire_episode_01_r3()
    manifest = compile_episode_bundle(episode, output)
    print(f"title={episode.title}")
    print(f"duration={episode.duration_s}s scenes={len(episode.scenes)} shots={len(episode.shots)}")
    print(f"manifest={manifest['manifest_sha256']}")
    print(f"player={output / 'episode-01.html'}")
