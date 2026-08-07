from pathlib import Path
from omega_summary_fractal_t.render import write_bundle
from omega_summary_fractal_t.summarizer import SummaryEngine
root=Path(__file__).resolve().parents[1]
bundle=SummaryEngine(root,max_files=5000).generate(depth=4,audience="oak")
for kind,path in write_bundle(bundle,root/"reports"/"omega-summary-fractal-demo").items(): print(kind,path)
