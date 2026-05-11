from pathlib import Path
from typing import List

from loguru import logger
from .config import Config


class RetentionManager:
    """Manage backup retention by deleting oldest archives beyond the limit."""

    def __init__(self, config: Config):
        self.config = config
        self._log = logger.bind(phase="retention")

    def apply(self) -> List[Path]:
        """Enforce retention: sort by mtime, keep N most recent, delete rest."""
        cfg = self.config
        pattern = cfg.file_pattern
        
        archives = sorted(
            [p for p in cfg.dest.glob(pattern) if p.is_file()],
            key=lambda p: p.stat().st_mtime,
        )

        if not archives:
            self._log.info("No existing backups found for retention check")
            return []

        keep = cfg.backup.retention
        if len(archives) <= keep:
            self._log.info(f"Retention OK  ({len(archives)} ≤ {keep})")
            return []

        to_delete = archives[:-keep]
        self._log.warning(
            f"Retention: {len(archives)} exist, max {keep}, "
            f"deleting {len(to_delete)} oldest"
        )

        deleted: List[Path] = []
        for archive in to_delete:
            if self.config.dry_run:
                self._log.info(f"[DRY-RUN] Would delete: {archive.name}")
            else:
                try:
                    archive.unlink()
                    self._log.info(f"Deleted: {archive.name}")
                except OSError as exc:
                    self._log.error(f"Failed to delete {archive.name}: {exc}")
            deleted.append(archive)

        return deleted
