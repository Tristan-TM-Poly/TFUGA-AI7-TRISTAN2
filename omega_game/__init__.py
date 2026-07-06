"""Import shim for omega_game_t.omega_game."""

from pathlib import Path

_pkg = Path(__file__).resolve().parent.parent / "omega_game_t" / "omega_game"
if _pkg.exists():
    __path__.append(str(_pkg))

from omega_game_t.omega_game import *  # noqa: F401,F403,E402
