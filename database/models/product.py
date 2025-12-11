"""
Product model for database operations.
"""

from typing import Dict, Optional, Any
from datetime import datetime


class Product:
    """Product data model."""
    
    def __init__(
        self,
        url: str,
        title: Optional[str] = None,
        price: Optional[float] = None,
        brand: Optional[str] = None,
        rating: Optional[float] = None,
        availability: bool = False,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        self.title = title
        self.price = price
        self.brand = brand
        self.rating = rating
        self.availability = availability
        self.description = description
        self.image_url = image_url
        self.source = source
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "brand": self.brand,
            "rating": self.rating,
            "availability": self.availability,
            "description": self.description,
            "image_url": self.image_url,
            "source": self.source,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        """Create from dictionary."""
        return cls(
            url=data.get("url", ""),
            title=data.get("title"),
            price=data.get("price"),
            brand=data.get("brand"),
            rating=data.get("rating"),
            availability=data.get("availability", False),
            description=data.get("description"),
            image_url=data.get("image_url"),
            source=data.get("source"),
            metadata=data.get("metadata", {})
        )

