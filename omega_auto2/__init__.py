"""Import shim for omega_auto2_kernel.omega_auto2."""

from pathlib import Path

_kernel = Path(__file__).resolve().parent.parent / "omega_auto2_kernel" / "omega_auto2"
if _kernel.exists():
    __path__.append(str(_kernel))

from omega_auto2_kernel.omega_auto2 import *  # noqa: F401,F403,E402
