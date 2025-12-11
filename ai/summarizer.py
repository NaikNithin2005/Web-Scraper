"""
LLM Summarization Engine
Handles content summarization and structured data extraction.
"""

from typing import Dict, List, Optional, Any
from loguru import logger
import json


class Summarizer:
    """
    LLM-based summarization and extraction engine.
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
                logger.error("langchain_ollama not installed. Install with: pip install langchain-ollama")
                raise
        elif self.model_type == "openai":
            try:
                from langchain_openai import ChatOpenAI
                if not self.api_key:
                    raise ValueError("OpenAI API key required")
                self._model = ChatOpenAI(model=self.model_name, api_key=self.api_key)
            except ImportError:
                logger.error("langchain_openai not installed. Install with: pip install langchain-openai")
                raise
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        return self._model
    
    def summarize(self, content: str, max_length: int = 500) -> str:
        """
        Summarize content.
        
        Args:
            content: Content to summarize
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        model = self._get_model()
        
        # Truncate content if too long
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        prompt = f"""Summarize the following content in approximately {max_length} words. 
Focus on key points and important information.

Content:
{content}

Summary:"""
        
        try:
            if hasattr(model, 'invoke'):
                response = model.invoke(prompt)
                if isinstance(response, str):
                    return response
                elif hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
            else:
                # Fallback for different model interfaces
                return str(model(prompt))
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error generating summary: {e}"
    
    def extract_structured(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from content based on schema.
        
        Args:
            content: Content to extract from
            schema: Schema defining fields to extract
            
        Returns:
            Extracted data dict
        """
        model = self._get_model()
        
        schema_desc = json.dumps(schema, indent=2)
        
        prompt = f"""Extract the following information from the content and return as JSON.
Schema:
{schema_desc}

Content:
{content[:5000]}

Return only valid JSON matching the schema:"""
        
        try:
            if hasattr(model, 'invoke'):
                response = model.invoke(prompt)
                if isinstance(response, str):
                    response_text = response
                elif hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
            else:
                response_text = str(model(prompt))
            
            # Try to parse JSON from response
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return {}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {}
    
    def extract_keywords(self, content: str, count: int = 10) -> List[str]:
        """
        Extract keywords from content.
        
        Args:
            content: Content to extract keywords from
            count: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        model = self._get_model()
        
        prompt = f"""Extract the top {count} most important keywords from the following content.
Return them as a comma-separated list.

Content:
{content[:3000]}

Keywords:"""
        
        try:
            if hasattr(model, 'invoke'):
                response = model.invoke(prompt)
                if isinstance(response, str):
                    keywords_text = response
                elif hasattr(response, 'content'):
                    keywords_text = response.content
                else:
                    keywords_text = str(response)
            else:
                keywords_text = str(model(prompt))
            
            # Parse keywords
            keywords = [k.strip() for k in keywords_text.split(",")]
            return keywords[:count]
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

