import argparse,json
from pathlib import Path
from omega_capability_os_t import workunit_from_mapping
from omega_cognitive_computer_t import CognitiveComputer
from .compile import compile_report

def main()->int:
    p=argparse.ArgumentParser(description="Compile a canonical WorkUnit through TTM-EXEC R0.1")
    p.add_argument("workunit")
    a=p.parse_args()
    raw=json.loads(Path(a.workunit).read_text(encoding="utf-8"))
    wu=workunit_from_mapping(raw)
    print(json.dumps(compile_report(CognitiveComputer.default(),wu),indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
