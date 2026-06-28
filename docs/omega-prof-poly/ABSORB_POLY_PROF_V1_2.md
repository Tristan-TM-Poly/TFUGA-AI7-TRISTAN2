# Omega Absorb Poly Prof v1.2

Status: CLI output directory, GraphML, source selection and package status upgrade.

## Purpose

v1.2 extends the local CLI and export layer with output directory support, GraphML export, demo source selection, documentation index command and package status report.

```text
CLI
-> source selection
-> JSON exports
-> GraphML export
-> docs index
-> package status
-> local bundle writer with output directory
```

## New modules

- `source_selection.py`: selects demo source families: combined, polypublie, expertise.
- `package_status.py`: builds a package status Markdown report.

## Updated modules

- `cli.py`: adds `--source`, `--output-dir`, `graphml`, `docs-index`, `status`, and `sources`.
- `export_commands.py`: adds source-specific payloads and GraphML output.
- `__init__.py`: exports v1.2 helpers.
- `tests/test_omega_absorb_poly_prof_v11.py`: relaxed the version assertion for forward compatibility.

## CLI commands

```bash
omega-absorb sources
omega-absorb summary-json --source polypublie
omega-absorb validation-json --source expertise
omega-absorb graphml --source combined
omega-absorb docs-index
omega-absorb status
omega-absorb write-bundle --output-dir generated/custom_bundle
```

## Generated examples

- `generated/omega_absorb_poly_prof_v12/README.md`
- `generated/omega_absorb_poly_prof_v12/status.md`
- `generated/omega_absorb_poly_prof_v12/sources.txt`
- `generated/omega_absorb_poly_prof_v12/graph_export.graphml`

## Tests

```bash
python examples/omega_absorb_poly_prof_v12_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v12.py
```

## OAK boundary

- Source selection uses demo public metadata only.
- GraphML and JSON exports are local outputs.
- Bundle writing stays local to the selected output directory.
- External platform actions remain capability boundaries.

## v1.3 next targets

1. add CLI source file input for local JSON fixtures;
2. add compact table report command;
3. add combined JSON+GraphML bundle command;
4. add package health score;
5. add generated changelog from version manifest.
