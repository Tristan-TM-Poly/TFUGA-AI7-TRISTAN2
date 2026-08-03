from omega_web_hg_t.r03 import SearchIndex, compile_absorption

source_run = "generated/omega_web_hg_t_r02/example/runs/<run_id>"
output = "generated/omega_web_hg_t_r03/example"
bundle = compile_absorption(source_run, output)
print(bundle.report)

with SearchIndex(f"{output}/search.sqlite3") as index:
    print(index.query("preuve reproductible", limit=10))
