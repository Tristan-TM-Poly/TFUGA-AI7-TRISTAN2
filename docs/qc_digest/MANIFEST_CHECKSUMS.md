# Manifest and Checksums

Issue: #64

## Purpose

Record enough run metadata to make local digest outputs reproducible and auditable.

## Module

`local_digest.manifest`

## Manifest fields

- manifest version;
- run id;
- UTC creation time;
- package version;
- git commit;
- source adapter;
- query;
- filters;
- limits;
- review status;
- notes;
- output checksums;
- generated sample data flag.

## Checksum registry

Each output file gets:

- relative path;
- SHA-256;
- file size in bytes.

## Boundary

The manifest records local run facts. It does not certify truth, value, patentability, affiliation, or publication readiness.

## Tests

`tests/test_local_digest_manifest.py`
