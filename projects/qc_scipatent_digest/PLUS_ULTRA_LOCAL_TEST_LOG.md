# PLUS ULTRA Local Test Log

Environment: local ChatGPT container.

Commands executed:

```bash
python -m pytest -q
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v03
```

Observed results:

```text
2 passed
PLUS ULTRA complete
Documents: 6
Opportunities: 6
Bridges: 9
```

Generated v0.3 PLUS ULTRA outputs include:

- pipeline summary;
- OAK release assessment;
- DCT++ canon pack;
- reuse blueprints;
- entity clusters;
- entity warnings;
- dashboard;
- SQLite;
- science-IP bridges;
- review queue.
