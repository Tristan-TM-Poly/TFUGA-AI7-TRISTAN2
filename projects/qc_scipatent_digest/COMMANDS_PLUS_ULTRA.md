# Commands PLUS ULTRA

```bash
cd projects/qc_scipatent_digest
python -m pytest -q
python -m qc_scipatent_digest.cli demo --out outputs/demo
python -m qc_scipatent_digest.cli demo-max --out outputs/max
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra
python -m qc_scipatent_digest.cli build-plan --from-year 2022 --to-year 2026 --max-records 100 --mailto tardif.morency.tristan@gmail.com --out outputs/plan
```

Live commands must respect API terms, rate limits, copyright and OAK-IP gates.
