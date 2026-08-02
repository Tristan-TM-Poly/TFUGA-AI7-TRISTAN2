"""Compile the R1 studio bundle and print its evidence summary."""
from pathlib import Path
from omega_anime_studio_t import build_eighth_fire_r1, compile_project_bundle

if __name__ == '__main__':
    output = Path('generated/omega_anime_studio_t/eighth_fire_r1')
    manifest = compile_project_bundle(build_eighth_fire_r1(), output)
    print(f"project={manifest['project_id']}")
    print(f"shots={manifest['shot_count']}")
    print(f"matrix_cells={manifest['matrix_cell_count']}")
    print(f"sha256={manifest['manifest_sha256']}")
