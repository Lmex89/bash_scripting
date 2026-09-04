# Agent Instructions - scripts

Compact guide for OpenCode agents to avoid common mistakes.

## Python & Environment
- **Virtual Environment:** Always use `.venv_cron/bin/python` to execute Python scripts. Do NOT use default `python` or assume `.venv` exists.
- **Active Backup Script:** `backup.py` is the production backup orchestrator. `backup_dir.sh` is a legacy fallback; do not modify or run it.
- **Unused Config Duplicate:** The active configuration is loaded from `/home/lmex89/Documentos/scripts/config.ini` in the workspace root. The file `/home/lmex89/Documentos/scripts/backup/config.ini` is an unused duplicate; do not modify or read it for active settings.

## Codebase Exploration
- **Code Graph Mandatory:** Always use `codegraph_*` tools as a mandatory first step for search, symbol lookups, relationship tracing, and codebase exploration over generic search tools (like standard grep/glob).

## Hardcoded Credentials & Ignored Files
- **Secrets Warning:** `legacy/remove_urls.py` contains a hardcoded production `API_KEY` and `HOST`. It is gitignored; do not stage, commit, or expose its contents.

## System Dependencies
- **Backup Requirements:** Backup execution requires GNU `tar` and `pigz` (parallel gzip, installable via `sudo apt install pigz`) to be available on the host.

## Scripting Conventions
- **Bash Shebangs:** Use `#!/bin/bash` (not `#!/usr/bin/env bash`) for bash scripts in this repository, except for legacy `backup_dir.sh`.
