"""Generate and audit the canonical order-4 synthetic fixture."""
from tempfile import TemporaryDirectory
from omega_synergy_n_t.cli import main

if __name__ == "__main__":
    with TemporaryDirectory(prefix="omega-synergy-n-r2-") as directory:
        raise SystemExit(main(["demo","--fixture","synergy_os_order4","--output-dir",directory]))
