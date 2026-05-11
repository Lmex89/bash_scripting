#!/usr/bin/env python3
"""
Production-grade backup script for ~/Documentos -> /mnt/data/bkp.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from backup.config import Config, load_config
from backup.logger import setup_logging
from backup.lock import FileLock, LockError
from backup.validators import PreFlightValidator, PreFlightError
from backup.archiver import TarArchiver, IntegrityError, TarError
from backup.retention import RetentionManager
from backup.rollback import RollbackHandler
from backup.metrics import ExecutionMetrics


class SignalGuard:
    """Register handlers that clean up temp files and exit on SIGINT / SIGTERM."""

    def __init__(self, tmp_paths: list[Path]) -> None:
        self._tmp_paths = tmp_paths
        self._originals: dict[int, object] = {}

    def __enter__(self) -> SignalGuard:
        for sig in (signal.SIGINT, signal.SIGTERM):
            self._originals[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handler)
        return self

    def __exit__(self, *args: object) -> None:
        for sig, handler in self._originals.items():
            signal.signal(sig, handler)

    def _handler(self, signum: int, frame: object) -> None:
        sig_name = signal.Signals(signum).name
        log = logger.bind(phase="shutdown")
        log.critical(f"Received {sig_name}, cleaning up ...")
        for p in self._tmp_paths:
            try:
                if p.exists():
                    p.unlink()
                    log.info(f"Removed temp file: {p.name}")
            except OSError as exc:
                log.error(f"Failed to remove {p.name}: {exc}")
        sys.exit(128 + signum)


def run_backup(cfg: Config) -> ExecutionMetrics:
    """Main backup orchestration."""
    log = logger.bind(phase="backup")
    metrics = ExecutionMetrics()
    metrics.start_timer()

    log.info(f"Backup start: {cfg.source} -> {cfg.dest}")

    tmp_path = cfg.tmp_path
    final_path = cfg.final_path
    temp_files = [tmp_path]

    with SignalGuard(temp_files):
        # Pre-flight
        validator = PreFlightValidator(cfg)
        validator.validate_all()
        metrics.source_size = validator.estimate_source_size()

        # Clean stale temp files
        for stale in cfg.dest.glob(f"home_backup_*{tmp_path.suffix}"):
            log.warning(f"Removing stale temp: {stale.name}")
            if not cfg.dry_run:
                stale.unlink()

        # Dry-run: show intent and exit
        if cfg.dry_run:
            log.info(f"[DRY-RUN] Would create archive: {final_path.name}")
            retainer = RetentionManager(cfg)
            deleted = retainer.apply()
            metrics.deleted_count = len(deleted)
            metrics.success = True
            metrics.stop_timer()
            return metrics

        # Create archive
        archiver = TarArchiver(cfg)
        archiver.create_archive(tmp_path)

        # SHA256 of temp file
        log.info("Computing SHA256 ...")
        metrics.sha256 = TarArchiver.sha256_file(tmp_path)
        log.info(f"SHA256: {metrics.sha256}")

        # Atomic rename
        log.info(f"Finalizing: {tmp_path.name} -> {final_path.name}")
        os.rename(str(tmp_path), str(final_path))
        if not final_path.exists():
            raise IntegrityError(f"Rename failed: {final_path} does not exist")

        metrics.archive_size = final_path.stat().st_size

        # Verify tar integrity
        log.info("Verifying archive integrity ...")
        metrics.file_count = archiver.verify_archive(final_path)
        log.info(f"Archive OK  ({metrics.file_count} entries)")

        # Retention
        retainer = RetentionManager(cfg)
        deleted = retainer.apply()
        metrics.deleted_count = len(deleted)

        metrics.success = True
        metrics.stop_timer()
        log.success(
            f"Backup complete: {final_path.name} "
            f"({metrics.archive_size / (1024**3):.2f} GiB, "
            f"{metrics.file_count} files, "
            f"took {metrics.elapsed:.1f}s)"
        )

    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Production-grade backup for home directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Environment variables:\n"
            "  BACKUP_SOURCE       Source directory\n"
            "  BACKUP_DEST         Destination directory\n"
            "  BACKUP_RETENTION    Number of backups to keep\n"
            "  BACKUP_MIN_DISK_GB  Minimum free GiB required\n"
            "\n"
            "Examples:\n"
            "  %(prog)s                     Run with defaults\n"
            "  %(prog)s --source /data      Custom source\n"
            "  %(prog)s --dest /mnt/bkp     Custom destination\n"
        ),
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        metavar="PATH",
        help="Source directory (overrides config and env)",
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=None,
        metavar="PATH",
        help="Destination directory (overrides config and env)",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=None,
        metavar="N",
        help="Backups to keep (overrides config and env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the backup — no files written",
    )
    return parser


def config_from_args(args: argparse.Namespace, cfg: Config) -> Config:
    """Override config with CLI arguments."""
    if args.source is not None:
        cfg.backup.source = Path(args.source)
    if args.dest is not None:
        cfg.backup.dest = Path(args.dest)
    if args.retention is not None:
        cfg.backup.retention = args.retention
    if args.dry_run:
        cfg.dry_run = True
    return cfg


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Load config (priority: CLI args > env vars > config file > defaults)
    cfg = load_config()
    cfg = config_from_args(args, cfg)

    # Setup logging
    setup_logging(cfg)
    log = logger.bind(phase="main")

    log.info(
        f"Config: source={cfg.source}, dest={cfg.dest}, "
        f"retention={cfg.backup.retention}, "
        f"permission_strategy={cfg.tar.permission_strategy}"
    )

    try:
        with FileLock(cfg.lock.file):
            metrics = run_backup(cfg)

            log.bind(phase="metrics").info(
                "Backup metrics: " + json.dumps(metrics.to_dict())
            )

            if metrics.success:
                return 0
            log.error(f"Backup FAILED: {metrics.error}")
            return 1

    except LockError as exc:
        log.critical(str(exc))
        return 1
    except (PreFlightError, IntegrityError, TarError) as exc:
        log.critical(str(exc))
        return 1
    except Exception:
        log.critical("Unhandled exception", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
