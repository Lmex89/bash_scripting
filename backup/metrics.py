import time
from datetime import datetime, timezone
from typing import Optional


class ExecutionMetrics:
    """Collect and report backup execution metrics."""

    def __init__(self):
        self.start: float = 0.0
        self.end: float = 0.0
        self.source_size: Optional[int] = None
        self.archive_size: Optional[int] = None
        self.sha256: Optional[str] = None
        self.file_count: Optional[int] = None
        self.deleted_count: int = 0
        self.success: bool = False
        self.error: Optional[str] = None

    def start_timer(self) -> None:
        self.start = time.time()

    def stop_timer(self) -> None:
        self.end = time.time()

    @property
    def elapsed(self) -> float:
        return self.end - self.start if self.end > self.start else 0.0

    @property
    def compression_pct(self) -> Optional[float]:
        if self.source_size and self.archive_size and self.source_size > 0:
            return (1 - self.archive_size / self.source_size) * 100
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(self.elapsed, 2),
            "source_size_bytes": self.source_size,
            "archive_size_bytes": self.archive_size,
            "compression_ratio_pct": (
                round(self.compression_pct, 2) if self.compression_pct is not None else None
            ),
            "sha256": self.sha256,
            "file_count": self.file_count,
            "deleted_archives": self.deleted_count,
            "success": self.success,
            "error": self.error,
        }
