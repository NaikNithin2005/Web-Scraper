"""
Multi-Website Comparison Engine
Handles normalization of product data and comparison across multiple sources.
"""

from typing import Dict, List, Optional, Any
from loguru import logger
from datetime import datetime
import re


class ProductComparator:
    """
    Compares products across multiple websites.
    Normalizes product attributes and generates comparison reports.
    """
    
    def __init__(self):
        self.normalization_rules = {
            "price": self._normalize_price,
            "title": self._normalize_title,
            "brand": self._normalize_brand,
            "rating": self._normalize_rating,
            "availability": self._normalize_availability
        }
    
    def normalize_product(self, product: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalize product data from a source.
        
        Args:
            product: Raw product data
            source: Source website name
            
        Returns:
            Normalized product dict
        """
        normalized = {
            "source": source,
            "url": product.get("url", ""),
            "scraped_at": datetime.now().isoformat()
        }
        
        # Normalize each field
        for field, normalizer in self.normalization_rules.items():
            if field in product:
                normalized[field] = normalizer(product[field])
            else:
                normalized[field] = None
        
        # Copy other fields
        for key, value in product.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized
    
    def _normalize_price(self, price: Any) -> Optional[float]:
        """Normalize price to float."""
        if price is None:
            return None
        
        if isinstance(price, (int, float)):
            return float(price)
        
        # Extract number from string
        price_str = str(price)
        # Remove currency symbols and commas
        price_str = re.sub(r'[^\d.]', '', price_str)
        
        try:
            return float(price_str)
        except ValueError:
            logger.warning(f"Could not normalize price: {price}")
            return None
    
    def _normalize_title(self, title: Any) -> str:
        """Normalize product title."""
        if not title:
            return ""
        
        title_str = str(title).strip()
        # Remove extra whitespace
        title_str = re.sub(r'\s+', ' ', title_str)
        
        return title_str
    
    def _normalize_brand(self, brand: Any) -> str:
        """Normalize brand name."""
        if not brand:
            return ""
        
        brand_str = str(brand).strip().title()
        return brand_str
    
    def _normalize_rating(self, rating: Any) -> Optional[float]:
        """Normalize rating to float (0-5 scale)."""
        if rating is None:
            return None
        
        if isinstance(rating, (int, float)):
            # Assume 5-point scale if > 5, otherwise use as-is
            if rating > 5:
                return rating / 10.0  # Convert 10-point to 5-point
            return float(rating)
        
        # Extract number from string
        rating_str = str(rating)
        rating_match = re.search(r'(\d+\.?\d*)', rating_str)
        
        if rating_match:
            try:
                rating_val = float(rating_match.group(1))
                if rating_val > 5:
                    rating_val = rating_val / 10.0
                return rating_val
            except ValueError:
                pass
        
        return None
    
    def _normalize_availability(self, availability: Any) -> bool:
        """Normalize availability to boolean."""
        if availability is None:
            return False
        
        if isinstance(availability, bool):
            return availability
        
        availability_str = str(availability).lower()
        
        # Check for positive indicators
        positive_indicators = ["in stock", "available", "yes", "true", "1"]
        negative_indicators = ["out of stock", "unavailable", "no", "false", "0", "sold out"]
        
        for indicator in positive_indicators:
            if indicator in availability_str:
                return True
        
        for indicator in negative_indicators:
            if indicator in availability_str:
                return False
        
        return False
    
    def compare_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple products and generate comparison report.
        
        Args:
            products: List of normalized product dicts
            
        Returns:
            Comparison report dict
        """
        if not products:
            return {"error": "No products to compare"}
        
        # Normalize all products
        normalized = [self.normalize_product(p, p.get("source", "unknown")) for p in products]
        
        # Find best price
        prices = [p.get("price") for p in normalized if p.get("price") is not None]
        best_price = min(prices) if prices else None
        best_price_product = next(
            (p for p in normalized if p.get("price") == best_price),
            None
        )
        
        # Find highest rating
        ratings = [p.get("rating") for p in normalized if p.get("rating") is not None]
        best_rating = max(ratings) if ratings else None
        best_rating_product = next(
            (p for p in normalized if p.get("rating") == best_rating),
            None
        )
        
        # Find available products
        available_products = [p for p in normalized if p.get("availability", False)]
        
        # Calculate average price
        avg_price = sum(prices) / len(prices) if prices else None
        
        # Price difference analysis
        price_differences = {}
        if len(prices) > 1:
            for product in normalized:
                if product.get("price") is not None:
                    diff = product["price"] - best_price
                    price_differences[product["source"]] = {
                        "difference": diff,
                        "percentage": (diff / best_price * 100) if best_price else 0
                    }
        
        return {
            "total_products": len(normalized),
            "products": normalized,
            "best_price": {
                "price": best_price,
                "product": best_price_product
            },
            "best_rating": {
                "rating": best_rating,
                "product": best_rating_product
            },
            "available_count": len(available_products),
            "available_products": available_products,
            "average_price": avg_price,
            "price_differences": price_differences,
            "comparison_date": datetime.now().isoformat()
        }
    
    def find_best_value(self, products: List[Dict[str, Any]], 
                       price_weight: float = 0.6, 
                       rating_weight: float = 0.4) -> Optional[Dict[str, Any]]:
        """
        Find best value product based on price and rating.
        
        Args:
            products: List of normalized product dicts
            price_weight: Weight for price (0-1)
            rating_weight: Weight for rating (0-1)
            
        Returns:
            Best value product dict
        """
        if not products:
            return None
        
        normalized = [self.normalize_product(p, p.get("source", "unknown")) for p in products]
        
        # Filter products with both price and rating
        valid_products = [
            p for p in normalized 
            if p.get("price") is not None and p.get("rating") is not None
        ]
        
        if not valid_products:
            return None
        
        # Normalize scores (0-1 scale)
        prices = [p["price"] for p in valid_products]
        ratings = [p["rating"] for p in valid_products]
        
        min_price = min(prices)
        max_price = max(prices)
        min_rating = min(ratings)
        max_rating = max(ratings)
        
        # Calculate value scores
        best_product = None
        best_score = float('-inf')
        
        for product in valid_products:
            # Lower price is better (inverted)
            price_score = 1 - ((product["price"] - min_price) / (max_price - min_price)) if max_price != min_price else 1
            
            # Higher rating is better
            rating_score = (product["rating"] - min_rating) / (max_rating - min_rating) if max_rating != min_rating else 1
            
            # Combined score
            value_score = (price_score * price_weight) + (rating_score * rating_weight)
            
            if value_score > best_score:
                best_score = value_score
                best_product = product
        
        if best_product:
            best_product["value_score"] = best_score
        
        return best_product

