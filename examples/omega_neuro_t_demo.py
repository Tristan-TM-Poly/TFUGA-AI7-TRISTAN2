"""Executable example for Ω-NEURO-CELL-SYN-NET-T∞."""

import json

from omega_neuro_t.cli import build_demo


if __name__ == "__main__":
    print(json.dumps(build_demo(), indent=2, sort_keys=True))
