# Home Server Autonomous Builder — SAGE/TFUGA Zero-Touch Layer

**Date:** 2026-06-17  
**Scope:** turn a home PC into a controlled GitHub compute/cloud/autopilot node for the TFUGA / SAGE-TRISTAN ecosystem.  
**Safety posture:** autonomous creation of reports, branches, tests, artifacts, and draft PRs; no blind destructive writes to `main`.

## Purpose

This packet gives the repository a practical bridge from GitHub to a home PC:

1. build and test the repository continuously;
2. use the home PC as a self-hosted GitHub Actions runner when available;
3. run local autonomous scans that produce OAK/CVCD reports;
4. open safe draft PRs instead of silently mutating the canonical branch;
5. preserve a negative-memory ledger of blockers, missing tests, weak claims, and unsafe assumptions.

The repository already defines the operational path as:

```text
raw intuition -> formal object -> equation -> proof -> algorithm -> simulation -> prototype -> minimal fertile canon
```

This layer implements the server side of that metabolism.

## Architecture

```text
Home PC / Homelab Node
│
├─ GitHub self-hosted runner  [labels: self-hosted, linux, x64, home-lab]
├─ Docker / local services    [optional: Ollama, Nextcloud, Uptime Kuma]
├─ Autopilot scripts          [tools/autopilot/]
├─ Systemd timer              [runs local branch/PR generation]
├─ Reports                    [reports/autopilot/]
└─ GitHub PR factory          [gh CLI, safe branch push, draft PR]
```

## Autonomy Levels

| Level | Capability | Default policy |
| --- | --- | --- |
| 0 | Scan repository, generate report | enabled |
| 1 | Run tests / compile checks | enabled |
| 2 | Generate docs/manifests/reports | enabled |
| 3 | Commit to autopilot branch | local agent only |
| 4 | Open draft PR | local agent only |
| 5 | Merge to `main` | disabled unless explicitly enabled |
| 6 | Rotate secrets / change infra | disabled |

## What this push adds

- `.github/workflows/autonomous-ecosystem.yml` — portable GitHub Actions scan/build workflow with optional home-runner job.
- `tools/autopilot/autonomous_builder.py` — standard-library Python scanner that creates JSON/Markdown reports.
- `tools/autopilot/github_autopilot_agent.py` — local agent that can clone/pull, run checks, commit generated reports, push a branch, and open a draft PR.
- `tools/autopilot/home_server_bootstrap.sh` — homelab bootstrap template for Docker, GitHub CLI, UFW, Fail2ban, Tailscale placeholder, directories, and systemd timer templates.
- `ops/autonomy/home_server_autonomy_manifest.yml` — machine-readable OAK/CVCD/SAGE policy manifest.

## Safe local execution model

The home PC should run the local agent with a GitHub account/token that has only the minimum rights needed for the target repo.

```bash
python tools/autopilot/autonomous_builder.py --repo-root . --mode full
python tools/autopilot/github_autopilot_agent.py \
  --repo Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --workdir /srv/repos/TFUGA-AI7-TRISTAN2 \
  --branch-prefix autopilot/home-server \
  --open-pr
```

The agent defaults to safe behavior:

- it refuses to force-push;
- it generates a branch instead of writing directly to `main`;
- it records negative memory when tests or tooling are missing;
- it opens a draft PR when `--open-pr` is enabled;
- it does not touch secrets.

## OAK Guardrails

1. **No direct destructive operation on `main`.**
2. **No secret creation in repo files.**
3. **No claim promotion without status.**
4. **No result without report.**
5. **No autonomous merge unless explicitly enabled later.**
6. **Every failure becomes M_MINUS negative memory.**

## Home server checklist

```text
[ ] Ubuntu/Debian server installed
[ ] SSH protected by private VPN or LAN only
[ ] Docker installed
[ ] GitHub CLI installed and authenticated
[ ] GitHub self-hosted runner registered with label home-lab
[ ] systemd timer enabled for github_autopilot_agent.py
[ ] backups configured
[ ] secrets kept outside repository
```

## Expected result

After the home PC is connected, the ecosystem can:

- run CI on GitHub-hosted runners immediately;
- run heavier jobs on the home PC when the `home-lab` runner is online;
- create recurring OAK/CVCD build reports;
- produce draft PRs for autonomous improvements;
- keep the repository moving without requiring manual copy-paste workflows.
