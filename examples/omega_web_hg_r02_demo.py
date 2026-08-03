from omega_web_hg_t.r02 import IncrementalWebHypergraphCrawler, R02Config

config = R02Config(
    seed_url="https://example.org/",
    resource_budget=25,
    max_depth=4,
    delay_seconds=1.0,
)
bundle = IncrementalWebHypergraphCrawler(config).crawl("generated/omega_web_hg_t_r02/example-org")
print(bundle.oak_report())
