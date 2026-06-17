# Autopilot Tools

This directory contains the safe local/home-server layer for the TFUGA / SAGE-TRISTAN repository.

## Files

- `oak_cvcd_report.py` — safe report generator. It scans the repository and writes:
  - `reports/autopilot/autonomous_build_report.json`
  - `reports/autopilot/autonomous_build_report.md`
  - `reports/autopilot/m_minus_latest.json`
- `home_server_bootstrap.sh` — dry-run by default; prepares an Ubuntu/Debian PC for a future home runner.

## GitHub Actions

The workflow `.github/workflows/autonomous-ecosystem.yml` runs:

1. checkout;
2. Python setup;
3. pytest if `tests/` exists, otherwise compile check;
4. OAK/CVCD report generation;
5. artifact upload.

It also has a manual `home-lab` target that runs on:

```text
self-hosted, linux, x64, home-lab
```

## Safe autonomy policy

Autonomy is useful only when it stays verifiable.

```text
scan -> report -> branch -> draft PR -> checks -> human/canonical promotion
```

No script in this folder stores secrets. No script force-pushes. No script merges to `main`.

## Minimal local use

```bash
python3 tools/autopilot/oak_cvcd_report.py --repo-root . --mode scan
python3 tools/autopilot/oak_cvcd_report.py --repo-root . --mode full
```

## Home PC bootstrap dry-run

```bash
bash tools/autopilot/home_server_bootstrap.sh
```

Apply only on a PC you control:

```bash
bash tools/autopilot/home_server_bootstrap.sh --apply
```
