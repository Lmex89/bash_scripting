# scripts

Personal utility scripts for system maintenance and small tasks.

## Execution

- `.venv_cron/bin/python` runs Python scripts (`.venv_cron` instead of `.venv`).
- `backup.py` replaces `backup_dir.sh` — use the former, the latter exists only as safety net.
- Bash scripts use `#!/bin/bash` (not `#!/usr/bin/env bash`) except `backup_dir.sh` which uses the latter with `set -euo pipefail`.

## Data files misnamed as `.py`

- `id_soles.py` is **not valid Python** — it is a plain list of numeric IDs (comma-separated at top, newline-separated below). Do not try to import or run it.

## Hardcoded credentials

- `legacy/remove_urls.py` contains a hardcoded `API_KEY` and `HOST`. Treat with care; `.gitignore` prevents commits.

## Notable paths

| Path | Purpose |
|---|---|
| `backup.py` | Production-grade backup orchestrator (thin CLI + main logic) |
| `backup/` | Backup package: config, logger, lock, validators, archiver, retention, rollback, metrics |
| `config.ini.example` | Example configuration file — copy to `config.ini` and customize |
| `backup_dir.sh` | Legacy backup script — kept for safety, not actively used |
| `legacy/` | Deprecated scripts: Plex cleanup/sync, URL purge |
| `.venv_cron/` | Python 3.12 venv with `requests`, `loguru` |

## `backup.py` details

- **Modular**: SRP — each module handles one concern (config, logging, locking, validation, archiving, retention, rollback, metrics)
- **Config**: `config.ini` (INI format) → env vars (`BACKUP_*`) → CLI args (highest priority)
- **Pre-flight**: source exists, dest writable, disk ≥ 10 GiB free, permission scan, pigz availability
- **Permission strategy**: `skip` (default) or `strict` — `skip` uses `--ignore-failed-read` and logs warnings for unreadable files
- **Atomic**: tar → `.tmp` → SHA256 → rename to `.tar.gz`; `tar -tzf` verifies integrity
- **Retention**: sorted by mtime, keeps last N (default 3, `--retention` / `BACKUP_RETENTION`)
- **Rollback**: if new archive fails integrity, previous backup stays intact
- **Lock**: `fcntl.flock` at `/tmp/backup.lock` prevents concurrent runs
- **Signal**: SIGINT/SIGTERM cleans temp files, releases lock
- **Logging**: loguru — JSON file (rotation 10 MB, retention 30d) + colorized stderr
- **Dry-run**: `--dry-run` to simulate
- **Compression**: parallel gzip via `pigz` (default 4 threads, configurable)

### Cron (every 2 days at 04:00)

```
0 4 */2 * * /home/lmex89/Documentos/scripts/.venv_cron/bin/python /home/lmex89/Documentos/scripts/backup.py 2>&1 | logger -t backup
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BACKUP_SOURCE` | Source directory | `~/Documentos` |
| `BACKUP_DEST` | Destination directory | `/mnt/data/bkp` |
| `BACKUP_RETENTION` | Backups to keep | `3` |
| `BACKUP_MIN_DISK_GB` | Min free space required | `10` |
| `BACKUP_COMPRESSION_THREADS` | Parallel compression threads | `4` |

### System Dependencies

- `tar` (GNU tar) — archive creation
- `pigz` — parallel gzip compression (install: `sudo apt install pigz`)

## Background

- Only 2 git commits exist. No tests, no CI, no lint/typecheck config, no `README`.
- Cron is configured but does not reference any script in this directory (add cron entry above).
