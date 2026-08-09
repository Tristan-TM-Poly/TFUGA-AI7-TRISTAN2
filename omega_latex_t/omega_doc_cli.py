"""Compatibility entry point for the ``omega-doc`` project script.

The public command is an alias of the canonical Ω-LATEX-T∞ CLI. Keeping the
adapter tiny prevents a second command implementation from drifting away from
``omega_latex_t.cli`` while satisfying the repository's declared project
script surface.
"""
from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
