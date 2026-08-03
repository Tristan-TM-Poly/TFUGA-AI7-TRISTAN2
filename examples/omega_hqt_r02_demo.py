from pathlib import Path
from omega_hqt_t.r02.campaign import run_r02_benchmark, write_r02_bundle

if __name__ == "__main__":
    report = run_r02_benchmark(hours=24)
    print(report.status, report.evidence_hash)
    print(write_r02_bundle(Path("generated/omega_hqt_t/r0.2")))
