"""
Price Tracking System
Handles historical price storage, alerts, and price analysis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from database.db import Database


class PriceTracker:
    """
    Price tracking system with historical storage and alerts.
    """
    
    def __init__(self, db: Database):
        """
        Initialize price tracker.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.alert_thresholds = {}  # product_id -> threshold config
    
    def track_product(self, product_data: Dict[str, Any]) -> int:
        """
        Track a product and record its price.
        
        Args:
            product_data: Product data dict
            
        Returns:
            Product ID
        """
        product_id = self.db.insert_product(product_data)
        
        # Record price history
        if product_data.get("price") is not None:
            self.db.add_price_history(
                product_id,
                product_data["price"],
                product_data.get("currency", "USD")
            )
        
        logger.info(f"Tracking product: {product_data.get('title', product_data.get('url'))}")
        return product_id
    
    def get_price_history(self, product_id: int, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get price history for a product.
        
        Args:
            product_id: Product ID
            days: Number of days to look back (None for all)
            
        Returns:
            List of price history records
        """
        history = self.db.get_price_history(product_id)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            history = [
                h for h in history
                if datetime.fromisoformat(h["recorded_at"]) >= cutoff_date
            ]
        
        return history
    
    def get_price_trend(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze price trend.
        
        Args:
            product_id: Product ID
            days: Number of days to analyze
            
        Returns:
            Trend analysis dict
        """
        history = self.get_price_history(product_id, days)
        
        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "current_price": history[0]["price"] if history else None,
                "change_percent": 0
            }
        
        # Sort by date (oldest first)
        history_sorted = sorted(history, key=lambda x: x["recorded_at"])
        
        first_price = history_sorted[0]["price"]
        last_price = history_sorted[-1]["price"]
        
        change = last_price - first_price
        change_percent = (change / first_price * 100) if first_price > 0 else 0
        
        # Determine trend
        if change_percent > 5:
            trend = "increasing"
        elif change_percent < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calculate statistics
        prices = [h["price"] for h in history_sorted]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        return {
            "trend": trend,
            "current_price": last_price,
            "first_price": first_price,
            "change": change,
            "change_percent": change_percent,
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "data_points": len(history)
        }
    
    def set_alert(self, product_id: int, threshold_type: str, threshold_value: float):
        """
        Set price alert.
        
        Args:
            product_id: Product ID
            threshold_type: "drop" or "increase"
            threshold_value: Percentage threshold
        """
        self.alert_thresholds[product_id] = {
            "type": threshold_type,
            "value": threshold_value
        }
        logger.info(f"Alert set for product {product_id}: {threshold_type} {threshold_value}%")
    
    def check_alerts(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Check if any alerts should be triggered.
        
        Args:
            product_id: Product ID
            
        Returns:
            List of triggered alerts
        """
        if product_id not in self.alert_thresholds:
            return []
        
        threshold = self.alert_thresholds[product_id]
        history = self.get_price_history(product_id, days=7)
        
        if len(history) < 2:
            return []
        
        # Get current and previous price
        current_price = history[0]["price"]
        previous_price = history[1]["price"] if len(history) > 1 else current_price
        
        if previous_price == 0:
            return []
        
        change_percent = ((current_price - previous_price) / previous_price) * 100
        
        alerts = []
        
        if threshold["type"] == "drop" and change_percent <= -threshold["value"]:
            alerts.append({
                "type": "price_drop",
                "product_id": product_id,
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": change_percent,
                "threshold": threshold["value"]
            })
        elif threshold["type"] == "increase" and change_percent >= threshold["value"]:
            alerts.append({
                "type": "price_increase",
                "product_id": product_id,
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": change_percent,
                "threshold": threshold["value"]
            })
        
        return alerts
    
    def normalize_product_attributes(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize product attributes for comparison.
        
        Args:
            product: Raw product data
            
        Returns:
            Normalized product data
        """
        normalized = {
            "url": product.get("url", ""),
            "title": self._normalize_title(product.get("title", "")),
            "price": self._normalize_price(product.get("price")),
            "brand": self._normalize_brand(product.get("brand", "")),
            "rating": self._normalize_rating(product.get("rating")),
            "availability": self._normalize_availability(product.get("availability", False)),
            "source": product.get("source", "unknown")
        }
        
        # Copy other fields
        for key, value in product.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized
    
    def _normalize_title(self, title: str) -> str:
        """Normalize product title."""
        if not title:
            return ""
        return " ".join(title.split())
    
    def _normalize_price(self, price: Any) -> Optional[float]:
        """Normalize price to float."""
        if price is None:
            return None
        if isinstance(price, (int, float)):
            return float(price)
        
        import re
        price_str = str(price)
        price_str = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(price_str)
        except ValueError:
            return None
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name."""
        if not brand:
            return ""
        return brand.strip().title()
    
    def _normalize_rating(self, rating: Any) -> Optional[float]:
        """Normalize rating to float (0-5 scale)."""
        if rating is None:
            return None
        if isinstance(rating, (int, float)):
            return float(rating) if rating <= 5 else rating / 10.0
        
        import re
        rating_str = str(rating)
        match = re.search(r'(\d+\.?\d*)', rating_str)
        if match:
            try:
                val = float(match.group(1))
                return val if val <= 5 else val / 10.0
            except ValueError:
                pass
        return None
    
    def _normalize_availability(self, availability: Any) -> bool:
        """Normalize availability to boolean."""
        if isinstance(availability, bool):
            return availability
        
        avail_str = str(availability).lower()
        positive = ["in stock", "available", "yes", "true", "1"]
        return any(indicator in avail_str for indicator in positive)

