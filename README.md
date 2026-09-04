# scripts

Personal utility scripts for system maintenance.

## Scripts

| Script | Purpose |
|---|---|
| `backup.py` | Production-grade backup of `~/Documentos` → `/mnt/data/bkp/` (atomic writes, integrity checks, retention) |
| `backup_dir.sh` | Legacy backup — kept as safety net |

## Setup

Python virtual environment at `.venv_cron/` (Python 3.12) with `requests` and `loguru`.

### System Requirements

- GNU `tar`
- `pigz` (parallel gzip) — install with `sudo apt install pigz`

## Usage

```bash
# Backup (dry-run first)
./.venv_cron/bin/python backup.py --dry-run

# Full backup
./.venv_cron/bin/python backup.py

# Custom retention
./.venv_cron/bin/python backup.py --retention 5

# Override compression threads (env var)
BACKUP_COMPRESSION_THREADS=8 ./.venv_cron/bin/python backup.py
```

### Configuration

Copy `config.ini.example` to `config.ini` and customize:

```ini
[backup]
source = ~/Documentos
dest = /mnt/data/bkp
retention = 3
min_disk_gb = 10
tar_timeout = 3600
compression_threads = 4  # parallel gzip threads
```

## Features

- **Atomic writes**: tar → `.tmp` → SHA256 → rename (prevents corruption)
- **Integrity checks**: SHA256 hash + `tar -tzf` verification
- **Retention management**: keeps last N backups (default 3)
- **Parallel compression**: `pigz` with 4 threads (3-4× faster than gzip)
- **Pre-flight validation**: source/dest checks, disk space, permissions
- **Lock file**: prevents concurrent backup runs
- **Structured logging**: JSON logs with rotation (10 MB, 30 days)
- **Dry-run mode**: simulate backup without writing files
- **Configurable**: INI file, environment variables, CLI args

## Cron

Every 2 days at 04:00:

```
0 4 */2 * * /home/lmex89/Documentos/scripts/.venv_cron/bin/python /home/lmex89/Documentos/scripts/backup.py 2>&1 | logger -t backup
```

## Performance

Parallel compression with `pigz` (4 threads):
- **3-4× faster** than single-threaded gzip
- Same `.tar.gz` format (fully compatible)
- Configurable via `compression_threads` in `config.ini` or `BACKUP_COMPRESSION_THREADS` env var
