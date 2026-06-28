# Rosette Command Atlas

`rosette-atlas` emits a machine-readable and Markdown command atlas from `pyproject.toml`.

## Command

```bash
rosette-atlas --out out_atlas/command_atlas.json --markdown out_atlas/COMMAND_ATLAS.md
```

## What it records

- package version
- command count
- command name
- entrypoint
- Rosette layer
- purpose
- documentation hint
- missing metadata/docs warnings

## OAK status

- `atlas_passed_not_certified`
- `atlas_review_needed`

## CI integration

The Rosette-Tristan CI now runs:

```bash
rosette-atlas --out out_atlas/command_atlas.json --markdown out_atlas/COMMAND_ATLAS.md
```

The generated atlas is uploaded in the `rosette-ci-reports` artifact.

## OAK lock

The atlas verifies command registration and documentation hints. It does not prove runtime correctness, PDF fidelity, mathematical equivalence or scientific truth.
