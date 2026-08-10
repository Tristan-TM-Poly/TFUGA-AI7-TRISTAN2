from omega_recycle import StockRecord, aggregate_recoverable_stock


def test_urban_mine_aggregation() -> None:
    records = (StockRecord("montreal", 2026, "copper", 100.0, 0.8), StockRecord("montreal", 2026, "copper", 50.0, 0.5), StockRecord("quebec", 2026, "copper", 40.0, 1.0))
    result = aggregate_recoverable_stock(records)
    assert result[("montreal", 2026, "copper")] == 105.0
    assert result[("quebec", 2026, "copper")] == 40.0
