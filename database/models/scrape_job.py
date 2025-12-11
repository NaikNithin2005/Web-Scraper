"""
Scrape job model.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    """Scrape job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeJob:
    """Scrape job model."""
    
    def __init__(
        self,
        url: str,
        method: str = "auto",
        status: str = "pending",
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        self.url = url
        self.method = method
        self.status = status
        self.result = result
        self.error = error
        self.started_at = started_at
        self.completed_at = completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

