import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path("config.ini")


@dataclass
class BackupConfig:
    source: Path = Path.home() / "Documentos"
    dest: Path = Path("/mnt/data/bkp")
    retention: int = 3
    min_disk_gb: int = 10
    tar_timeout: int = 3600


@dataclass
class TarConfig:
    permission_strategy: str = "skip"  # strict or skip


@dataclass
class LoggingConfig:
    log_file: Path = Path("backup.log")
    rotation: str = "10 MB"
    retention_days: int = 30
    console_level: str = "INFO"
    file_level: str = "DEBUG"


@dataclass
class LockConfig:
    file: Path = Path("/tmp/backup.lock")


@dataclass
class Config:
    backup: BackupConfig = field(default_factory=BackupConfig)
    tar: TarConfig = field(default_factory=TarConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    lock: LockConfig = field(default_factory=LockConfig)
    dry_run: bool = False

    @property
    def dest(self) -> Path:
        """Get the destination path."""
        return self.backup.dest

    @property
    def source(self) -> Path:
        """Get the source path."""
        return self.backup.source

    @property
    def timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d_%H-%M")

    @property
    def filename(self) -> str:
        """Get the backup filename."""
        return f"home_backup_{self.timestamp}.tar.gz"

    @property
    def file_pattern(self) -> str:
        """Get the glob pattern for backup files."""
        return "home_backup_*.tar.gz"

    @property
    def tmp_path(self) -> Path:
        """Get the temporary backup path."""
        return self.dest / f"{self.filename}.tmp"

    @property
    def final_path(self) -> Path:
        """Get the final backup path."""
        return self.dest / self.filename

    @property
    def log_path(self) -> Path:
        """Get the absolute log file path."""
        p = self.logging.log_file
        if p.is_absolute():
            return p
        return self.dest / p


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file, environment variables, with defaults."""
    cfg = Config()
    
    # 1. Load from config file
    if config_path is None:
        config_path = CONFIG_FILE
    
    parser = configparser.ConfigParser()
    if config_path.exists():
        parser.read(config_path)
        
        # Backup section
        if parser.has_section("backup"):
            section = parser["backup"]
            if "source" in section:
                cfg.backup.source = Path(section["source"]).expanduser()
            if "dest" in section:
                cfg.backup.dest = Path(section["dest"])
            if "retention" in section:
                cfg.backup.retention = int(section["retention"])
            if "min_disk_gb" in section:
                cfg.backup.min_disk_gb = int(section["min_disk_gb"])
            if "tar_timeout" in section:
                cfg.backup.tar_timeout = int(section["tar_timeout"])
        
        # Tar section
        if parser.has_section("tar"):
            section = parser["tar"]
            if "permission_strategy" in section:
                strategy = section["permission_strategy"].lower()
                if strategy in ("strict", "skip"):
                    cfg.tar.permission_strategy = strategy

        # Logging section
        if parser.has_section("logging"):
            section = parser["logging"]
            if "log_file" in section:
                cfg.logging.log_file = Path(section["log_file"])
            if "rotation" in section:
                cfg.logging.rotation = section["rotation"]
            if "retention_days" in section:
                cfg.logging.retention_days = int(section["retention_days"])
            if "console_level" in section:
                cfg.logging.console_level = section["console_level"].upper()
            if "file_level" in section:
                cfg.logging.file_level = section["file_level"].upper()

        # Lock section
        if parser.has_section("lock"):
            section = parser["lock"]
            if "file" in section:
                cfg.lock.file = Path(section["file"])

    # 2. Override with Environment Variables
    if env_src := os.environ.get("BACKUP_SOURCE"):
        cfg.backup.source = Path(env_src)
    if env_dest := os.environ.get("BACKUP_DEST"):
        cfg.backup.dest = Path(env_dest)
    if env_ret := os.environ.get("BACKUP_RETENTION"):
        cfg.backup.retention = int(env_ret)
    if env_min_disk := os.environ.get("BACKUP_MIN_DISK_GB"):
        cfg.backup.min_disk_gb = int(env_min_disk)

    return cfg
