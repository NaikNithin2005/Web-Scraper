"""
AI Service Module
Main AI service for LLM integration, summarization, and data extraction.
"""

from typing import Dict, List, Optional, Any
from loguru import logger
from .summarizer import Summarizer
from .intent_engine import IntentEngine


class AIService:
    """
    Main AI service integrating LLM capabilities for scraping.
    """
    
    def __init__(
        self,
        model_type: str = "ollama",
        model_name: str = "llama3",
        api_key: Optional[str] = None
    ):
        """
        Initialize AI service.
        
        Args:
            model_type: "ollama", "openai", "mistral", etc.
            model_name: Model name/identifier
            api_key: API key for cloud-based models
        """
        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        
        self.summarizer = Summarizer(model_type, model_name, api_key)
        self.intent_engine = IntentEngine(model_type, model_name, api_key)
    
    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        Summarize content using LLM.
        
        Args:
            content: Content to summarize
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        return self.summarizer.summarize(content, max_length)
    
    def extract_data(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from content using AI.
        
        Args:
            content: Content to extract from
            schema: Schema defining what to extract
            
        Returns:
            Extracted data dict
        """
        return self.summarizer.extract_structured(content, schema)
    
    def understand_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Understand user intent and determine scraping strategy.
        
        Args:
            user_prompt: User's natural language prompt
            
        Returns:
            Intent dict with strategy recommendations
        """
        return self.intent_engine.analyze_intent(user_prompt)
    
    def generate_comparison_report(self, products: List[Dict[str, Any]]) -> str:
        """
        Generate AI-powered comparison report.
        
        Args:
            products: List of product dicts to compare
            
        Returns:
            Comparison report text
        """
        # Format products for LLM
        products_text = "\n\n".join([
            f"Product from {p.get('source', 'unknown')}:\n"
            f"Title: {p.get('title', 'N/A')}\n"
            f"Price: {p.get('price', 'N/A')}\n"
            f"Rating: {p.get('rating', 'N/A')}\n"
            f"Availability: {p.get('availability', 'N/A')}"
            for p in products
        ])
        
        prompt = f"""Compare these products and provide a detailed analysis:
        
{products_text}

Provide:
1. Best value recommendation
2. Price comparison
3. Feature differences
4. Overall recommendation"""
        
        return self.summarizer.summarize(products_text, max_length=1000)
    
    def detect_anomalies(self, price_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in price history using AI.
        
        Args:
            price_history: List of price records
            
        Returns:
            List of detected anomalies
        """
        if len(price_history) < 3:
            return []
        
        # Calculate price changes
        anomalies = []
        for i in range(1, len(price_history)):
            prev_price = price_history[i-1].get("price", 0)
            curr_price = price_history[i].get("price", 0)
            
            if prev_price > 0:
                change_percent = ((curr_price - prev_price) / prev_price) * 100
                
                # Detect significant changes (>20% drop or >30% increase)
                if change_percent < -20:
                    anomalies.append({
                        "type": "price_drop",
                        "change_percent": change_percent,
                        "previous_price": prev_price,
                        "current_price": curr_price,
                        "date": price_history[i].get("date")
                    })
                elif change_percent > 30:
                    anomalies.append({
                        "type": "price_spike",
                        "change_percent": change_percent,
                        "previous_price": prev_price,
                        "current_price": curr_price,
                        "date": price_history[i].get("date")
                    })
        
        return anomalies

