from omega_web_hg_t.core import CrawlConfig, WebHypergraphCrawler

config = CrawlConfig(
    seed_url="https://example.org/",
    page_budget=10,
    delay_seconds=1.0,
)
result = WebHypergraphCrawler(config).crawl()
result.write("generated/omega_web_hg_t/example-org")
print(result.oak_report())
