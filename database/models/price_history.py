"""
Price history model.
"""

from typing import Optional
from datetime import datetime


class PriceHistory:
    """Price history entry model."""
    
    def __init__(
        self,
        product_id: int,
        price: float,
        currency: str = "USD",
        recorded_at: Optional[datetime] = None
    ):
        self.product_id = product_id
        self.price = price
        self.currency = currency
        self.recorded_at = recorded_at or datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "product_id": self.product_id,
            "price": self.price,
            "currency": self.currency,
            "recorded_at": self.recorded_at.isoformat()
        }

