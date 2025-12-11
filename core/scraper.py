"""
Universal Scraper Module
Handles request management, automatic mode-switching, and flexible scraping pipeline.
"""

import requests
import cloudscraper
from typing import Dict, Optional, Any, List
from loguru import logger
from .browser import BrowserManager
from .anti_block import AntiBlockEngine


class UniversalScraper:
    """
    Universal scraper with automatic mode-switching:
    requests → cloudscraper → Playwright/Selenium
    """
    
    def __init__(self, use_browser: bool = False, anti_block: Optional[AntiBlockEngine] = None):
        self.use_browser = use_browser
        self.anti_block = anti_block or AntiBlockEngine()
        self.browser_manager = BrowserManager() if use_browser else None
        self.session = requests.Session()
        self.cloudscraper_session = cloudscraper.create_scraper()
        
    def scrape(
        self,
        url: str,
        method: str = "auto",
        headers: Optional[Dict] = None,
        timeout: int = 30,
        retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scrape a URL with automatic mode-switching.
        
        Args:
            url: Target URL
            method: "auto", "requests", "cloudscraper", or "browser"
            headers: Custom headers
            timeout: Request timeout
            retries: Number of retry attempts
            **kwargs: Additional arguments
            
        Returns:
            Dict with 'html', 'status_code', 'method_used', 'headers'
        """
        headers = headers or {}
        headers.update(self.anti_block.get_headers())
        
        for attempt in range(retries):
            try:
                if method == "auto":
                    result = self._scrape_auto(url, headers, timeout, **kwargs)
                elif method == "requests":
                    result = self._scrape_requests(url, headers, timeout, **kwargs)
                elif method == "cloudscraper":
                    result = self._scrape_cloudscraper(url, headers, timeout, **kwargs)
                elif method == "browser":
                    result = self._scrape_browser(url, headers, timeout, **kwargs)
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                logger.info(f"Successfully scraped {url} using {result['method_used']}")
                return result
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt == retries - 1:
                    raise
                self.anti_block.wait_before_retry(attempt)
        
        raise Exception(f"Failed to scrape {url} after {retries} attempts")
    
    def _scrape_auto(self, url: str, headers: Dict, timeout: int, **kwargs) -> Dict[str, Any]:
        """Auto-select best scraping method."""
        # Try requests first
        try:
            return self._scrape_requests(url, headers, timeout, **kwargs)
        except Exception as e:
            logger.debug(f"Requests failed, trying cloudscraper: {e}")
        
        # Try cloudscraper
        try:
            return self._scrape_cloudscraper(url, headers, timeout, **kwargs)
        except Exception as e:
            logger.debug(f"Cloudscraper failed, trying browser: {e}")
        
        # Fallback to browser
        if self.browser_manager:
            return self._scrape_browser(url, headers, timeout, **kwargs)
        else:
            raise Exception("All scraping methods failed and browser not available")
    
    def _scrape_requests(self, url: str, headers: Dict, timeout: int, **kwargs) -> Dict[str, Any]:
        """Scrape using requests library."""
        response = self.session.get(url, headers=headers, timeout=timeout, **kwargs)
        response.raise_for_status()
        
        return {
            "html": response.text,
            "status_code": response.status_code,
            "method_used": "requests",
            "headers": dict(response.headers),
            "url": response.url
        }
    
    def _scrape_cloudscraper(self, url: str, headers: Dict, timeout: int, **kwargs) -> Dict[str, Any]:
        """Scrape using cloudscraper (Cloudflare bypass)."""
        response = self.cloudscraper_session.get(url, headers=headers, timeout=timeout, **kwargs)
        response.raise_for_status()
        
        return {
            "html": response.text,
            "status_code": response.status_code,
            "method_used": "cloudscraper",
            "headers": dict(response.headers),
            "url": response.url
        }
    
    def _scrape_browser(self, url: str, headers: Dict, timeout: int, **kwargs) -> Dict[str, Any]:
        """Scrape using browser automation."""
        if not self.browser_manager:
            raise Exception("Browser manager not initialized")
        
        html = self.browser_manager.scrape_page(url, headers=headers, timeout=timeout, **kwargs)
        
        return {
            "html": html,
            "status_code": 200,
            "method_used": "browser",
            "headers": headers,
            "url": url
        }
    
    def close(self):
        """Clean up resources."""
        if self.browser_manager:
            self.browser_manager.close()
        self.session.close()

