# Demo Data Generator

Issue: #60

## Purpose

Create deterministic generated sample data for local tests, tutorials, and dry-runs.

This generator does not use private data.

## Module

```bash
python -m local_digest.demo_data --seed 7 --count 8 --output outputs/demo_digest
```

## Output files

```text
outputs/demo_digest/
  demo_dataset.json
  demo_publications.json
  demo_patent_records.json
  demo_institutions.json
  demo_topics.json
```

## Records

The generated dataset includes:

- demo publications;
- demo invention records;
- demo institutions;
- demo topics.

Every record includes `generated_sample_data: true`.

## OAK boundary

- synthetic sample data only;
- not evidence;
- not a real institution dataset;
- not a patentability or commercial claim;
- safe for tests and tutorials.

## Reproducibility

The same seed and count produce the same output.
