#!/usr/bin/env bash
set -euo pipefail

# Configuration
BACKUP_DIR="/mnt/data/bkp"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M")"
FILENAME="home_backup_${TIMESTAMP}.tar.gz"
SOURCE_DIR="$HOME/Documentos"
LOG_FILE="${BACKUP_DIR}/backup_dir.log"

log() {
  local message="$1"
  echo "$(date +"%Y-%m-%d %H:%M:%S") [backup_dir] ${message}" | tee -a "$LOG_FILE"
}

error_handler() {
  local exit_code=$?
  log "ERROR: line ${LINENO}, exit code ${exit_code}"
  exit "$exit_code"
}

trap error_handler ERR

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

log "Start backup. source=${SOURCE_DIR} dest=${BACKUP_DIR}/${FILENAME}"

# Create TAR.GZ backup
tar -czf "${BACKUP_DIR}/${FILENAME}" \
  --exclude="${BACKUP_DIR}" \
  -C "$HOME" "Documentos"

# Retention: keep only last 3 backups
cd "$BACKUP_DIR"

if ls home_backup_*.tar.gz >/dev/null 2>&1; then
  ls -1t home_backup_*.tar.gz 2>/dev/null | tail -n +4 | while read -r file; do
    if [ -n "$file" ] && [ -f "$file" ]; then
      log "Deleting old backup: ${BACKUP_DIR}/${file}"
      rm -f -- "$file"
    fi
  done
fi

log "Backup completed: ${BACKUP_DIR}/${FILENAME}"
