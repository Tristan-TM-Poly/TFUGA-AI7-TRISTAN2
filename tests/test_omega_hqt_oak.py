from omega_hqt_t.oak import run_oak_benchmarks

def test_oakbench_passes():
    report=run_oak_benchmarks(8); assert report.passed; assert report.status=="CERTIFIED_SYNTHETIC_PUBLIC_RESEARCH_KERNEL_R0_1"; assert report.metrics["outcomes"]==48
