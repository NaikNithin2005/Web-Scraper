"""
DOM Parsing Engine
Handles flexible DOM parsing with XPath, CSS selectors, and BeautifulSoup.
"""

from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Any, Union
from loguru import logger
import re
from lxml import etree


class DOMParser:
    """
    Flexible DOM parsing engine supporting multiple selector types.
    """
    
    def __init__(self, html: str, parser: str = "html.parser"):
        """
        Initialize parser with HTML content.
        
        Args:
            html: HTML content to parse
            parser: Parser type ("html.parser", "lxml", "html5lib")
        """
        self.soup = BeautifulSoup(html, parser)
        self.html = html
        
        # Create lxml tree for XPath support
        try:
            self.lxml_tree = etree.HTML(html)
        except Exception as e:
            logger.warning(f"Failed to create lxml tree: {e}")
            self.lxml_tree = None
    
    def find_by_css(self, selector: str, first: bool = False) -> Union[List[Tag], Tag, None]:
        """
        Find elements using CSS selector.
        
        Args:
            selector: CSS selector string
            first: Return first match only
            
        Returns:
            List of elements or single element
        """
        elements = self.soup.select(selector)
        
        if first:
            return elements[0] if elements else None
        return elements
    
    def find_by_xpath(self, xpath: str, first: bool = False) -> Union[List, Any, None]:
        """
        Find elements using XPath.
        
        Args:
            xpath: XPath expression
            first: Return first match only
            
        Returns:
            List of elements or single element
        """
        if not self.lxml_tree:
            logger.error("XPath requires lxml tree, but it's not available")
            return None
        
        try:
            elements = self.lxml_tree.xpath(xpath)
            
            if first:
                return elements[0] if elements else None
            return elements
        except Exception as e:
            logger.error(f"XPath error: {e}")
            return None
    
    def find_by_text(self, text: str, exact: bool = False) -> List[Tag]:
        """
        Find elements containing specific text.
        
        Args:
            text: Text to search for
            exact: Exact match (True) or contains (False)
            
        Returns:
            List of matching elements
        """
        if exact:
            return self.soup.find_all(string=re.compile(f"^{re.escape(text)}$"))
        else:
            return self.soup.find_all(string=re.compile(re.escape(text)))
    
    def extract_text(self, selector: Optional[str] = None, clean: bool = True) -> str:
        """
        Extract text content from elements.
        
        Args:
            selector: Optional CSS selector to narrow down
            clean: Clean whitespace
            
        Returns:
            Extracted text
        """
        if selector:
            elements = self.find_by_css(selector)
            if not elements:
                return ""
            text = " ".join([elem.get_text() for elem in elements])
        else:
            text = self.soup.get_text()
        
        if clean:
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_attributes(self, selector: str, attributes: List[str]) -> List[Dict[str, str]]:
        """
        Extract specific attributes from elements.
        
        Args:
            selector: CSS selector
            attributes: List of attribute names to extract
            
        Returns:
            List of dicts with attribute values
        """
        elements = self.find_by_css(selector)
        results = []
        
        for elem in elements:
            result = {}
            for attr in attributes:
                result[attr] = elem.get(attr, "")
            results.append(result)
        
        return results
    
    def extract_links(self, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract all links from the page.
        
        Args:
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of dicts with 'url' and 'text'
        """
        links = self.find_by_css("a")
        results = []
        
        for link in links:
            href = link.get("href", "")
            if base_url and href.startswith("/"):
                href = base_url.rstrip("/") + href
            
            results.append({
                "url": href,
                "text": link.get_text(strip=True),
                "title": link.get("title", "")
            })
        
        return results
    
    def extract_images(self, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract all images from the page.
        
        Args:
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of dicts with 'src', 'alt', 'title'
        """
        images = self.find_by_css("img")
        results = []
        
        for img in images:
            src = img.get("src", "") or img.get("data-src", "")
            if base_url and src.startswith("/"):
                src = base_url.rstrip("/") + src
            
            results.append({
                "src": src,
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "width": img.get("width", ""),
                "height": img.get("height", "")
            })
        
        return results
    
    def extract_meta_tags(self) -> Dict[str, str]:
        """
        Extract meta tags from the page.
        
        Returns:
            Dict with meta tag names and values
        """
        meta_tags = {}
        
        # Standard meta tags
        for meta in self.find_by_css("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content", "")
            
            if name:
                meta_tags[name] = content
        
        return meta_tags
    
    def extract_structured_data(self) -> List[Dict[str, Any]]:
        """
        Extract structured data (JSON-LD, microdata, etc.).
        
        Returns:
            List of structured data objects
        """
        structured_data = []
        
        # Extract JSON-LD
        json_ld_scripts = self.find_by_css("script[type='application/ld+json']")
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                structured_data.append({"type": "json-ld", "data": data})
            except Exception as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")
        
        return structured_data
    
    def clean_html(self, remove_scripts: bool = True, remove_styles: bool = True) -> str:
        """
        Clean HTML by removing scripts, styles, etc.
        
        Args:
            remove_scripts: Remove script tags
            remove_styles: Remove style tags
            
        Returns:
            Cleaned HTML string
        """
        soup = self.soup.__copy__()
        
        if remove_scripts:
            for script in soup(["script"]):
                script.decompose()
        
        if remove_styles:
            for style in soup(["style"]):
                style.decompose()
        
        return str(soup)
    
    def get_body_text(self, separator: str = "\n") -> str:
        """
        Get text content from body tag.
        
        Args:
            separator: Separator between text blocks
            
        Returns:
            Cleaned text content
        """
        body = self.soup.find("body")
        if not body:
            return ""
        
        # Remove scripts and styles
        for tag in body(["script", "style"]):
            tag.decompose()
        
        text = body.get_text(separator=separator, strip=True)
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text

