# Omega Patent Thesis T — Usage

Status: C scaffold.

## Run with the built-in example

```bash
python -m omega_patent_thesis_t demo
python -m omega_patent_thesis_t summary
python -m omega_patent_thesis_t export
```

## Run with a JSON seed

```bash
python -m omega_patent_thesis_t summary --input examples/patent_thesis_seed_example.json
python -m omega_patent_thesis_t export --input examples/patent_thesis_seed_example.json
```

## Test the module

```bash
python -m pytest tests/test_omega_patent_cli.py tests/test_omega_patent_io.py
```

## Boundary

The CLI produces a structured review pack. It does not provide legal conclusions, product validation, or external technical validation.

## M-minus

Usability requires a module entrypoint, a seed loader, an example JSON file, and CLI tests. Pass 6 adds those pieces without changing repository configuration.
