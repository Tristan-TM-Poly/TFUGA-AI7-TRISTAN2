#!/usr/bin/env bash
# Ω-HOSTING-T — conservative Ubuntu 24.04 VPS bootstrap
#
# Purpose:
#   Prepare a fresh VPS for Docker-based n8n/proxy deployment.
#
# Safety:
#   - No secrets are created here.
#   - The script does not deploy n8n.
#   - SSH is allowed before the firewall is enabled.
#   - Read before running on a real server.

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root or with sudo." >&2
  exit 1
fi

if ! command -v lsb_release >/dev/null 2>&1; then
  apt-get update
  apt-get install -y lsb-release
fi

CODENAME="$(lsb_release -cs)"
if [[ "${CODENAME}" != "noble" ]]; then
  echo "Warning: expected Ubuntu 24.04 noble, got ${CODENAME}. Continuing cautiously." >&2
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get upgrade -y
apt-get install -y \
  ca-certificates \
  curl \
  git \
  jq \
  ufw \
  fail2ban \
  unattended-upgrades \
  docker.io \
  docker-compose-v2

systemctl enable --now docker
systemctl enable --now fail2ban
systemctl enable --now unattended-upgrades

mkdir -p /opt/omega-hosting/{compose,backups,logs,restore,oak-ledger}
chmod 750 /opt/omega-hosting

# Firewall baseline. Keep SSH open before enabling.
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

cat >/opt/omega-hosting/README.txt <<'EOF'
Ω-HOSTING-T VPS root directory.

Subdirectories:
- compose: Docker Compose files copied from GitHub after review.
- backups: local backup staging area before encrypted off-server copy.
- logs: operational logs.
- restore: restore scripts and notes.
- oak-ledger: append-only deployment notes and OAK decisions.

Do not store long-term secrets in this file tree.
EOF

cat <<'EOF'
Bootstrap complete.
Next steps:
1. Confirm DNS points to the VPS.
2. Copy reviewed compose files to /opt/omega-hosting/compose.
3. Create runtime environment values on the VPS only.
4. Start with reverse proxy + n8n only after OAK review.
EOF
