import hashlib
import subprocess
from pathlib import Path

from loguru import logger
from .config import Config


class IntegrityError(Exception):
    """Archive integrity check failed."""


class TarError(Exception):
    """tar command failed."""


class TarArchiver:
    """Create and verify tar archives."""

    def __init__(self, config: Config):
        self.config = config
        self._log = logger.bind(phase="archiver")

    def create_archive(self, tmp_path: Path) -> None:
        """Create a tar.gz archive of the source directory."""
        cfg = self.config
        src = cfg.source
        dest = cfg.dest

        self._log.info(f"Creating archive: {tmp_path.name}")

        cmd = [
            "tar",
            "-czf", str(tmp_path),
            "--exclude", str(dest),
            "-C", str(src.parent),
            src.name,
        ]

        for pattern in cfg.tar.exclude:
            cmd.extend(["--exclude", pattern])
            self._log.debug(f"Exclude pattern added: {pattern}")

        if cfg.tar.permission_strategy == "skip":
            cmd.append("--ignore-failed-read")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=cfg.backup.tar_timeout,
            )
            
            if result.returncode == 0:
                tmp_size = tmp_path.stat().st_size
                self._log.info(f"Archive created  ({tmp_size / (1024**3):.2f} GiB)")
            elif result.returncode == 1:
                # Warnings (skipped files with --ignore-failed-read)
                self._log.warning(f"Archive created with warnings: {result.stderr}")
            else:
                raise TarError(
                    f"tar failed (exit {result.returncode}): {result.stderr.strip()}"
                )
        except subprocess.TimeoutExpired:
            raise TarError(f"tar timed out after {cfg.backup.tar_timeout}s")

    def verify_archive(self, path: Path) -> int:
        """Verify archive integrity and return file count."""
        self._log.info(f"Verifying archive integrity: {path.name}")
        try:
            result = subprocess.run(
                ["tar", "-tzf", str(path)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise IntegrityError(
                    f"tar integrity check FAILED for {path.name}: {result.stderr.strip()}"
                )
            file_count = len(result.stdout.splitlines())
            self._log.info(f"Archive OK  ({file_count} entries)")
            return file_count
        except subprocess.TimeoutExpired:
            raise IntegrityError(f"Archive verification timed out for {path.name}")

    @staticmethod
    def sha256_file(path: Path) -> str:
        """Compute SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
