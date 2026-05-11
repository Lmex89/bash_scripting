from pathlib import Path
from typing import List

from loguru import logger
from .config import Config


class RollbackHandler:
    """Handle rollback when a backup fails integrity check."""

    def __init__(self, config: Config):
        self.config = config
        self._log = logger.bind(phase="rollback")

    def attempt_restore(self, failed_path: Path) -> bool:
        """
        Attempt to find a valid previous backup.
        Returns True if a valid previous backup exists, False otherwise.
        """
        cfg = self.config
        pattern = cfg.file_pattern

        # Get all valid backups (excluding the failed one), sorted newest first
        backups = sorted(
            [p for p in cfg.dest.glob(pattern) if p.is_file() and p != failed_path],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            self._log.critical(
                f"Archive {failed_path.name} FAILED integrity check, "
                f"but NO previous backup exists to restore"
            )
            return False

        previous = backups[0]
        self._log.warning(
            f"Archive {failed_path.name} FAILED integrity check, "
            f"previous backup intact: {previous.name} "
            f"({previous.stat().st_size / (1024**3):.2f} GiB)"
        )
        return True
