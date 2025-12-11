"""
Plugin System Module
Allows custom extractors for specific websites and rule-based scraping templates.
"""

from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from loguru import logger
import importlib
import inspect
from pathlib import Path


class BaseExtractor(ABC):
    """
    Base class for custom extractors.
    All extractors should inherit from this class.
    """
    
    @abstractmethod
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract data from HTML.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Extracted data dictionary
        """
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if extractor can handle this URL
        """
        pass
    
    def get_name(self) -> str:
        """Get extractor name."""
        return self.__class__.__name__


class PluginManager:
    """
    Manages custom extractors and scraping plugins.
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        """
        Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugin files
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.extractors: List[BaseExtractor] = []
        self.templates: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Plugin manager initialized with plugins directory: {plugins_dir}")
    
    def register_extractor(self, extractor: BaseExtractor):
        """
        Register a custom extractor.
        
        Args:
            extractor: Extractor instance
        """
        if not isinstance(extractor, BaseExtractor):
            raise ValueError("Extractor must inherit from BaseExtractor")
        
        self.extractors.append(extractor)
        logger.info(f"Registered extractor: {extractor.get_name()}")
    
    def load_plugins_from_directory(self):
        """Load all plugins from the plugins directory."""
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return
        
        # Load Python files
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue
            
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")
    
    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file."""
        module_name = plugin_file.stem
        
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {plugin_file}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find all BaseExtractor subclasses
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseExtractor) and 
                obj != BaseExtractor):
                extractor = obj()
                self.register_extractor(extractor)
                logger.info(f"Loaded extractor {name} from {plugin_file}")
    
    def get_extractor_for_url(self, url: str) -> Optional[BaseExtractor]:
        """
        Get the best extractor for a given URL.
        
        Args:
            url: URL to extract from
            
        Returns:
            Extractor instance or None
        """
        for extractor in self.extractors:
            if extractor.can_handle(url):
                return extractor
        return None
    
    def register_template(self, name: str, template: Dict[str, Any]):
        """
        Register a scraping template.
        
        Args:
            name: Template name
            template: Template configuration dict with:
                - selectors: CSS/XPath selectors
                - fields: Field extraction rules
                - rules: Custom extraction rules
        """
        self.templates[name] = template
        logger.info(f"Registered template: {name}")
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_extractors(self) -> List[str]:
        """List all registered extractors."""
        return [ext.get_name() for ext in self.extractors]
    
    def list_templates(self) -> List[str]:
        """List all registered templates."""
        return list(self.templates.keys())


# Example extractor implementations

class AmazonExtractor(BaseExtractor):
    """Example extractor for Amazon product pages."""
    
    def can_handle(self, url: str) -> bool:
        return "amazon.com" in url or "amazon.in" in url
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "url": url,
            "source": "amazon"
        }
        
        # Extract title
        title_elem = soup.select_one("#productTitle")
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        
        # Extract price
        price_elem = soup.select_one(".a-price-whole, .a-offscreen")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Remove currency symbols and convert to float
            import re
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                data["price"] = float(price_match.group().replace(',', ''))
        
        # Extract rating
        rating_elem = soup.select_one("#acrPopover .a-icon-alt")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            import re
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                data["rating"] = float(rating_match.group(1))
        
        # Extract availability
        availability_elem = soup.select_one("#availability span")
        if availability_elem:
            avail_text = availability_elem.get_text(strip=True).lower()
            data["availability"] = "in stock" in avail_text or "available" in avail_text
        
        return data


class FlipkartExtractor(BaseExtractor):
    """Example extractor for Flipkart product pages."""
    
    def can_handle(self, url: str) -> bool:
        return "flipkart.com" in url
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "url": url,
            "source": "flipkart"
        }
        
        # Extract title
        title_elem = soup.select_one("span.B_NuCI")
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        
        # Extract price
        price_elem = soup.select_one("div._30jeq3._16Jk6d")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            import re
            price_match = re.search(r'[\d,]+', price_text)
            if price_match:
                data["price"] = float(price_match.group().replace(',', ''))
        
        # Extract rating
        rating_elem = soup.select_one("div._3LWZlK")
        if rating_elem:
            try:
                data["rating"] = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass
        
        return data


# Import importlib.util for plugin loading
import importlib.util

