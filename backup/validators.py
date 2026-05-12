import os
import subprocess
from pathlib import Path
from typing import List, Optional

from loguru import logger
from .config import Config


class PreFlightError(Exception):
    """Pre-flight validation failure — abort."""


class PermissionValidator:
    """Check source tree for unreadable files."""

    @staticmethod
    def scan_unreadable(path: Path) -> List[Path]:
        """Return list of files/directories the current user cannot read."""
        unreadable = []
        for root, dirs, files in os.walk(path):
            for name in files + dirs:
                full = Path(root) / name
                if not os.access(str(full), os.R_OK):
                    unreadable.append(full)
        return unreadable


class PreFlightValidator:
    """Pre-flight validation checks."""

    def __init__(self, config: Config):
        self.config = config
        self._log = logger.bind(phase="preflight")

    def validate_all(self) -> None:
        """Run all pre-flight validations."""
        self._validate_source()
        self._validate_destination()
        self._validate_disk_space()
        self._validate_permissions()
        self._validate_compression()
        self._log.info("All pre-flight checks passed")

    def _validate_source(self) -> None:
        src = self.config.source
        if not src.exists():
            raise PreFlightError(f"Source does not exist: {src}")
        if not src.is_dir():
            raise PreFlightError(f"Source is not a directory: {src}")
        if not os.access(str(src), os.R_OK):
            raise PreFlightError(f"Source is not readable: {src}")
        self._log.info(f"Source OK  ({src})")

    def _validate_destination(self) -> None:
        dest = self.config.dest
        if not dest.exists():
            if self.config.dry_run:
                self._log.info(f"[DRY-RUN] Would create destination: {dest}")
            else:
                self._log.warning(f"Destination does not exist, creating: {dest}")
                dest.mkdir(parents=True, exist_ok=True)
        if not dest.is_dir():
            raise PreFlightError(f"Destination is not a directory: {dest}")
        if not os.access(str(dest), os.W_OK):
            raise PreFlightError(f"Destination is not writable: {dest}")
        self._log.info(f"Destination OK  ({dest})")

    def _validate_disk_space(self) -> None:
        dest = self.config.dest
        try:
            st = os.statvfs(str(dest))
            free_gb = (st.f_frsize * st.f_bavail) / (1024**3)
            if free_gb < self.config.backup.min_disk_gb:
                raise PreFlightError(
                    f"Low disk space: {free_gb:.1f} GiB free, "
                    f"need ≥{self.config.backup.min_disk_gb} GiB on {dest}"
                )
            self._log.info(f"Disk space OK  ({free_gb:.1f} GiB free)")
        except OSError as exc:
            raise PreFlightError(f"Cannot check disk space: {exc}")

    def _validate_permissions(self) -> None:
        """Check for unreadable files and handle based on permission_strategy."""
        src = self.config.source
        strategy = self.config.tar.permission_strategy
        
        unreadable = PermissionValidator.scan_unreadable(src)
        if not unreadable:
            self._log.info("Permission scan: all files readable")
            return

        if strategy == "strict":
            for p in unreadable:
                self._log.error(f"Unreadable file: {p}")
            raise PreFlightError(
                f"Found {len(unreadable)} unreadable files (permission_strategy=strict)"
            )
        
        # strategy == "skip"
        for p in unreadable:
            self._log.warning(f"Skipping unreadable file: {p}")
        self._log.warning(
            f"Found {len(unreadable)} unreadable files (permission_strategy=skip)"
        )

    def _validate_compression(self) -> None:
        """Verify pigz is available for parallel compression."""
        try:
            result = subprocess.run(
                ["pigz", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise PreFlightError("pigz not found - required for parallel compression")
            version = result.stdout.splitlines()[0] if result.stdout else "unknown"
            self._log.info(f"Compression OK  (pigz {version})")
        except FileNotFoundError:
            raise PreFlightError("pigz not installed - install with: sudo apt install pigz")
        except subprocess.TimeoutExpired:
            raise PreFlightError("pigz version check timed out")

    def estimate_source_size(self) -> Optional[int]:
        """Estimate source directory size in bytes."""
        try:
            result = subprocess.run(
                ["du", "-sb", str(self.config.source)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return int(result.stdout.split()[0])
        except (subprocess.SubprocessError, ValueError, IndexError, OSError):
            pass
        return None
