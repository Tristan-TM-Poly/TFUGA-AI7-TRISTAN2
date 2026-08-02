# Ω-SOLID-T∞ R0.2 quick start

```bash
python -m pytest -q tests/test_omega_solids_r02.py
python -m pytest -q tests/test_omega_solids_scale_r02.py
python -m omega_solids_t.cli manifest
python -m omega_solids_t.cli decode 424242 --environment 2
python -m omega_solids_t.cli oak 424242 --environment 2
python -m omega_solids_t.cli search "porosity"
```

The checked-in atlas contains 20,480 generated logical objects. They are not certified material records.
