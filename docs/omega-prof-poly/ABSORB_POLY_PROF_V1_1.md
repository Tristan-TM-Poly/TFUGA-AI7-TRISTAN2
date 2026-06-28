# Omega Absorb Poly Prof v1.1

Status: CLI export, writer and documentation index upgrade.

## Purpose

v1.1 extends the stable local CLI with JSON and graph export commands, adds a local release bundle writer, creates a packaged documentation index and adds a root `pyproject.toml` entry point.

```text
CLI
-> summary JSON
-> validation JSON
-> graph JSON
-> release bundle writer
-> documentation index
```

## New modules

- `export_commands.py`: builds summary, validation and graph JSON payloads.
- `release_bundle_writer.py`: writes release bundle files to a local target directory.
- `documentation_index.py`: provides a packaged documentation index.

## CLI commands

```bash
omega-absorb version
omega-absorb demo
omega-absorb roadmap
omega-absorb summary-json
omega-absorb validation-json
omega-absorb graph-json
omega-absorb write-bundle
```

Equivalent module commands:

```bash
python -m omega_prof_poly_t.cli summary-json
python -m omega_prof_poly_t.cli validation-json
python -m omega_prof_poly_t.cli graph-json
python -m omega_prof_poly_t.cli write-bundle
```

## Generated examples

- `generated/omega_absorb_poly_prof_v11/README.md`
- `generated/omega_absorb_poly_prof_v11/documentation_index.md`
- `generated/omega_absorb_poly_prof_v11/validation_report.json`
- `generated/omega_absorb_poly_prof_v11/graph_export.json`

## Tests

```bash
python examples/omega_absorb_poly_prof_v11_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v11.py
```

## OAK boundary

- Export payloads use demo public metadata.
- Writer utility writes local files only.
- CLI commands do not perform external platform actions.

## v1.2 next targets

1. add CLI argument for output directory;
2. add GraphML CLI export;
3. add source selection argument;
4. add documentation index command;
5. add generated package status report.
