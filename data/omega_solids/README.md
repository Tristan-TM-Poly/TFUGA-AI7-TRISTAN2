# Ω-SOLID-T∞ data seeds

The package generates twelve deterministic `SolidGenome-T` fixtures from `omega_solids_t.atlas`.

They are intentionally broad ontology and pipeline test cases. Numerical values are illustrative seeds with explicit uncertainty and a warning source string. They are not certified reference data and must not be used for engineering release, safety decisions, procurement, medical use, critical structures, or scientific claims without replacement by traceable datasets.

Generate them on demand with:

```bash
python -m omega_solids_t.cli emit-archetypes --output-dir data/omega_solids/archetypes
```

The generated manifest records each genome fingerprint. CI round-trips every archetype through JSON and verifies that the canonical fingerprint is preserved.
