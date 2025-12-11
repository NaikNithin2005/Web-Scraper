"""
Database layer for the AI-driven web scraper.
"""

from .db import Database
from .models.product import Product
from .models.price_history import PriceHistory
from .models.scrape_job import ScrapeJob
from .models.user_session import UserSession

__all__ = [
    "Database",
    "Product",
    "PriceHistory",
    "ScrapeJob",
    "UserSession"
]

