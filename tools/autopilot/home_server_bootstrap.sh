#!/usr/bin/env bash
# Home Server Bootstrap Template for TFUGA / SAGE-TRISTAN
# Safe default: dry-run. Use --apply only on your own Ubuntu/Debian PC.

set -euo pipefail

MODE="dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  MODE="apply"
fi

say() { printf '[home-server-bootstrap] %s\n' "$*"; }
run() {
  if [[ "$MODE" == "apply" ]]; then
    say "running: $*"
    "$@"
  else
    say "dry-run: $*"
  fi
}

say "mode=$MODE"
say "This script prepares a local PC for Docker, GitHub CLI, reports, and a future self-hosted runner."
say "It does not store GitHub tokens and does not register the runner by itself."

run sudo apt-get update
run sudo apt-get install -y git curl ca-certificates gnupg ufw fail2ban docker.io docker-compose-plugin gh python3 python3-venv python3-pip
run sudo usermod -aG docker "${USER}"

run sudo mkdir -p /srv/repos /srv/agents /srv/homelab /srv/backups /srv/models
run sudo chown -R "${USER}:${USER}" /srv/repos /srv/agents /srv/homelab /srv/backups /srv/models

run sudo ufw allow OpenSSH
run sudo ufw --force enable

cat <<'EOF'

Next manual-safe steps, because they require account/device authorization:

1. Authenticate GitHub CLI:
   gh auth login

2. Register GitHub self-hosted runner from GitHub UI:
   Repo -> Settings -> Actions -> Runners -> New self-hosted runner
   Use labels: self-hosted, linux, x64, home-lab

3. Optional private access:
   Install Tailscale and avoid exposing SSH directly to the public Internet.

4. Optional local cloud/AI services:
   Use Docker Compose under /srv/homelab.

5. Test the repo build locally:
   git clone https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2.git /srv/repos/TFUGA-AI7-TRISTAN2
   cd /srv/repos/TFUGA-AI7-TRISTAN2
   python3 tools/autopilot/oak_cvcd_report.py --repo-root . --mode full
EOF
