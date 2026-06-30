#!/usr/bin/env bash
# Ω-HOSTING-T — n8n Postgres backup skeleton
#
# This script assumes the Docker Compose project is already running on the VPS.
# It writes a local dump file. Off-server encrypted copy is a separate OAK step.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/omega-hosting/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-/opt/omega-hosting/compose/docker-compose.n8n.yml}"
PROJECT_NAME="${PROJECT_NAME:-omega_n8n}"
DB_NAME="${POSTGRES_DB:-n8n}"
DB_USER="${POSTGRES_USER:-n8n}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${BACKUP_DIR}/n8n-postgres-${STAMP}.dump"

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T postgres \
  pg_dump -Fc -U "${DB_USER}" "${DB_NAME}" > "${OUT}"

chmod 600 "${OUT}"
sha256sum "${OUT}" > "${OUT}.sha256"

echo "Backup written: ${OUT}"
echo "Next OAK step: copy this backup to encrypted off-server storage and test restore."
