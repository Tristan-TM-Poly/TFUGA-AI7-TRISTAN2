# Manifest and Checksums

Issue: #64

Module: `local_digest.manifest`

Purpose: record local run metadata and file hashes.

## Records

- run id
- UTC time
- package version
- git commit
- source adapter
- query
- filters
- limits
- review status
- file paths
- SHA-256 hashes
- file sizes

## Tests

`tests/test_local_digest_manifest.py`
