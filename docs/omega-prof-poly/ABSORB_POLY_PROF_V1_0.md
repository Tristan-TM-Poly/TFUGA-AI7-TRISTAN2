# Omega Absorb Poly Prof v1.0

Status: stable local release for the public research absorption pipeline.

## Purpose

v1.0 packages the v0.3 through v0.9 work into a stable local CLI, release bundle, version manifest, generated examples and smoke tests.

```text
public/demo metadata
-> validation
-> absorption
-> opportunity compilation
-> portfolio selection
-> roadmap
-> release bundle
-> CLI
```

## New modules

- `cli.py`: stable local CLI with `version`, `demo` and `roadmap` commands.
- `version_manifest.py`: release lineage from v0.3 to v1.0.
- `release_bundle.py`: deterministic release summary and roadmap bundle.

## Generated bundle

- `generated/omega_absorb_poly_prof_v10/README.md`
- `generated/omega_absorb_poly_prof_v10/release_summary.json`
- `generated/omega_absorb_poly_prof_v10/release_roadmap.md`
- `generated/omega_absorb_poly_prof_v10/version_manifest.md`

## Commands

```bash
python examples/omega_absorb_poly_prof_v10_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v10.py
python -m omega_prof_poly_t.cli version
python -m omega_prof_poly_t.cli demo
python -m omega_prof_poly_t.cli roadmap
```

## OAK boundary

- The release uses demo public metadata only.
- Claims remain test seeds, not truth.
- CLI outputs are local artifacts, not external actions.
- External connectors remain capability boundaries.

## v1.1 next targets

1. add CLI subcommands for JSON export and graph export;
2. add pyproject entry point;
3. add source registry validation report export;
4. add release bundle writer utility;
5. add packaged documentation index.
