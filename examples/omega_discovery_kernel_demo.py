"""Generate the Ω-DISCOVERY-KERNEL-T∞ Raman closed-loop bundle."""
from __future__ import annotations

from pathlib import Path

from omega_discovery_kernel_t import build_raman_closed_loop

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ledger = build_raman_closed_loop()
    output = ledger.write(ROOT / "generated/omega_discovery_kernel_t/raman-r0-1")
    audit = ledger.audit()
    print(f"Discovery bundle written to {output}")
    print(f"Ledger hash: {ledger.ledger_hash()}")
    print(f"Closed-loop coverage: {audit.metrics['closed_loop_coverage']}")
    print(f"Negative-memory coverage: {audit.metrics['negative_memory_coverage']}")


if __name__ == "__main__":
    main()
