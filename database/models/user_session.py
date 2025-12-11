"""
User session model.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class UserSession:
    """User session model."""
    
    def __init__(
        self,
        session_id: str,
        user_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        last_activity: Optional[datetime] = None
    ):
        self.session_id = session_id
        self.user_data = user_data or {}
        self.created_at = created_at or datetime.now()
        self.last_activity = last_activity or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_data": self.user_data,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

