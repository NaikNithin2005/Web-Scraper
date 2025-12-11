"""
Intent Understanding Engine
Analyzes user prompts to determine scraping strategy.
"""

from typing import Dict, List, Optional, Any
from loguru import logger
import re


class IntentEngine:
    """
    Analyzes user intent and recommends scraping strategies.
    """
    
    def __init__(
        self,
        model_type: str = "ollama",
        model_name: str = "llama3",
        api_key: Optional[str] = None
    ):
        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        self._model = None
    
    def _get_model(self):
        """Get or initialize LLM model."""
        if self._model:
            return self._model
        
        if self.model_type == "ollama":
            try:
                from langchain_ollama import OllamaLLM
                self._model = OllamaLLM(model=self.model_name)
            except ImportError:
                logger.error("langchain_ollama not installed")
                raise
        elif self.model_type == "openai":
            try:
                from langchain_openai import ChatOpenAI
                if not self.api_key:
                    raise ValueError("OpenAI API key required")
                self._model = ChatOpenAI(model=self.model_name, api_key=self.api_key)
            except ImportError:
                logger.error("langchain_openai not installed")
                raise
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        return self._model
    
    def analyze_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze user intent and determine scraping strategy.
        
        Args:
            user_prompt: User's natural language prompt
            
        Returns:
            Intent dict with strategy recommendations
        """
        # First, try rule-based analysis
        intent = self._rule_based_analysis(user_prompt)
        
        # Enhance with LLM if needed
        if intent.get("confidence", 0) < 0.7:
            intent = self._llm_analysis(user_prompt, intent)
        
        return intent
    
    def _rule_based_analysis(self, prompt: str) -> Dict[str, Any]:
        """Rule-based intent analysis."""
        prompt_lower = prompt.lower()
        
        intent = {
            "action": "scrape",
            "method": "auto",
            "features": [],
            "confidence": 0.5
        }
        
        # Detect action type
        if any(word in prompt_lower for word in ["compare", "comparison", "versus", "vs"]):
            intent["action"] = "compare"
            intent["features"].append("multi_scrape")
            intent["confidence"] += 0.2
        
        if any(word in prompt_lower for word in ["track", "monitor", "alert", "price history"]):
            intent["action"] = "track"
            intent["features"].append("scheduler")
            intent["features"].append("price_tracking")
            intent["confidence"] += 0.2
        
        if any(word in prompt_lower for word in ["summarize", "summary", "overview"]):
            intent["features"].append("summarization")
            intent["confidence"] += 0.1
        
        if any(word in prompt_lower for word in ["extract", "get", "find", "show"]):
            intent["features"].append("extraction")
            intent["confidence"] += 0.1
        
        # Detect method preference
        if any(word in prompt_lower for word in ["javascript", "dynamic", "spa", "react"]):
            intent["method"] = "browser"
            intent["confidence"] += 0.1
        
        if any(word in prompt_lower for word in ["fast", "quick", "simple"]):
            intent["method"] = "requests"
            intent["confidence"] += 0.1
        
        # Detect data types
        if any(word in prompt_lower for word in ["product", "item", "price", "buy"]):
            intent["data_type"] = "product"
            intent["features"].append("product_extraction")
            intent["confidence"] += 0.1
        
        if any(word in prompt_lower for word in ["article", "news", "blog", "text"]):
            intent["data_type"] = "article"
            intent["features"].append("text_extraction")
            intent["confidence"] += 0.1
        
        return intent
    
    def _llm_analysis(self, prompt: str, base_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance intent analysis using LLM."""
        try:
            model = self._get_model()
            
            analysis_prompt = f"""Analyze this user request for web scraping and provide a JSON response:
{{
    "action": "scrape|compare|track|extract",
    "method": "auto|requests|cloudscraper|browser",
    "data_type": "product|article|general",
    "features": ["list", "of", "features"],
    "confidence": 0.0-1.0
}}

User request: {prompt}

Return only valid JSON:"""
            
            if hasattr(model, 'invoke'):
                response = model.invoke(analysis_prompt)
                if isinstance(response, str):
                    response_text = response
                elif hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
            else:
                response_text = str(model(analysis_prompt))
            
            # Parse JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            import json
            llm_intent = json.loads(response_text)
            
            # Merge with base intent
            base_intent.update(llm_intent)
            return base_intent
            
        except Exception as e:
            logger.warning(f"LLM intent analysis failed: {e}, using rule-based only")
            return base_intent
    
    def recommend_strategy(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend scraping strategy based on intent.
        
        Args:
            intent: Intent dict from analyze_intent
            
        Returns:
            Strategy recommendations
        """
        strategy = {
            "scraper_method": intent.get("method", "auto"),
            "use_browser": intent.get("method") == "browser",
            "enable_ai": "summarization" in intent.get("features", []),
            "multi_scrape": "multi_scrape" in intent.get("features", []),
            "enable_tracking": "price_tracking" in intent.get("features", [])
        }
        
        return strategy

