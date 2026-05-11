# scripts

Personal utility scripts for system maintenance.

## Scripts

| Script | Purpose |
|---|---|
| `backup.py` | Production-grade backup of `~/Documentos` → `/mnt/data/bkp/` (atomic writes, integrity checks, retention) |
| `backup_dir.sh` | Legacy backup — kept as safety net |
| `entrevista.py` | Standalone coding exercise (character frequency counter) |

## Setup

Python virtual environment at `.venv_cron/` (Python 3.12) with `requests` and `loguru`.

## Usage

```bash
# Backup (dry-run first)
./.venv_cron/bin/python backup.py --dry-run

# Full backup
./.venv_cron/bin/python backup.py

# Custom retention
./.venv_cron/bin/python backup.py --retention 5
```

## Cron

Every 2 days at 04:00:

```
0 4 */2 * * /home/lmex89/Documentos/scripts/.venv_cron/bin/python /home/lmex89/Documentos/scripts/backup.py 2>&1 | logger -t backup
```

## Legacy

Deprecated scripts live in `legacy/`: Plex download cleanup/sync and URL purge.
