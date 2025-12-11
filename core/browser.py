"""
Browser Automation Engine
Handles Playwright-based scraping with headless browser, network interception, and lazy-loaded DOM handling.
"""

import asyncio
from typing import Dict, Optional, Any, List
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import time


class BrowserManager:
    """
    Manages browser automation using Playwright.
    Supports headless browsing, network interception, auto-scrolling, and authenticated scraping.
    """
    
    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        viewport: Optional[Dict] = None,
        user_agent: Optional[str] = None
    ):
        self.headless = headless
        self.browser_type = browser_type
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.user_agent = user_agent
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
    async def _init_browser(self):
        """Initialize browser and context."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        if not self.browser:
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unknown browser type: {self.browser_type}")
        
        if not self.context:
            context_options = {
                "viewport": self.viewport,
            }
            if self.user_agent:
                context_options["user_agent"] = self.user_agent
            
            self.context = await self.browser.new_context(**context_options)
    
    async def scrape_page_async(
        self,
        url: str,
        headers: Optional[Dict] = None,
        timeout: int = 30000,
        wait_until: str = "networkidle",
        auto_scroll: bool = True,
        intercept_network: bool = False,
        screenshots: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scrape a page asynchronously.
        
        Args:
            url: Target URL
            headers: Custom headers
            timeout: Page load timeout in ms
            wait_until: Wait condition ("load", "domcontentloaded", "networkidle")
            auto_scroll: Enable auto-scrolling for lazy-loaded content
            intercept_network: Capture network responses
            screenshots: Take screenshot of page
            **kwargs: Additional arguments
            
        Returns:
            Dict with 'html', 'screenshot', 'network_responses', 'url'
        """
        await self._init_browser()
        
        page = await self.context.new_page()
        network_responses = []
        
        try:
            # Set headers
            if headers:
                await page.set_extra_http_headers(headers)
            
            # Intercept network if requested
            if intercept_network:
                async def handle_response(response):
                    try:
                        network_responses.append({
                            "url": response.url,
                            "status": response.status,
                            "headers": await response.all_headers(),
                            "body": await response.text() if response.headers.get("content-type", "").startswith("text/") else None
                        })
                    except Exception as e:
                        logger.debug(f"Error intercepting response: {e}")
                
                page.on("response", handle_response)
            
            # Navigate to page
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            
            # Auto-scroll for lazy-loaded content
            if auto_scroll:
                await self._auto_scroll(page)
            
            # Wait a bit for any remaining dynamic content
            await page.wait_for_timeout(1000)
            
            # Get page content
            html = await page.content()
            
            result = {
                "html": html,
                "url": page.url,
                "title": await page.title(),
                "network_responses": network_responses if intercept_network else []
            }
            
            # Take screenshot if requested
            if screenshots:
                screenshot = await page.screenshot(full_page=True)
                result["screenshot"] = screenshot
            
            return result
            
        finally:
            await page.close()
    
    async def _auto_scroll(self, page: Page, scroll_delay: float = 0.5):
        """Auto-scroll page to load lazy content."""
        last_height = await page.evaluate("document.body.scrollHeight")
        
        while True:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(int(scroll_delay * 1000))
            
            # Calculate new height
            new_height = await page.evaluate("document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
        
        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
    
    def scrape_page(
        self,
        url: str,
        headers: Optional[Dict] = None,
        timeout: int = 30,
        **kwargs
    ) -> str:
        """
        Synchronous wrapper for scrape_page_async.
        Returns only HTML content.
        """
        timeout_ms = timeout * 1000
        result = asyncio.run(self.scrape_page_async(url, headers, timeout_ms, **kwargs))
        return result["html"]
    
    async def scrape_authenticated_async(
        self,
        url: str,
        login_url: str,
        login_selector: Dict[str, str],
        credentials: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scrape a page that requires authentication.
        
        Args:
            url: Target URL to scrape
            login_url: Login page URL
            login_selector: Dict with 'username_selector' and 'password_selector'
            credentials: Dict with 'username' and 'password'
            **kwargs: Additional arguments for scrape_page_async
            
        Returns:
            Dict with scraped content
        """
        await self._init_browser()
        
        page = await self.context.new_page()
        
        try:
            # Navigate to login page
            await page.goto(login_url)
            
            # Fill login form
            if "username_selector" in login_selector:
                await page.fill(login_selector["username_selector"], credentials["username"])
            if "password_selector" in login_selector:
                await page.fill(login_selector["password_selector"], credentials["password"])
            
            # Submit form
            if "submit_selector" in login_selector:
                await page.click(login_selector["submit_selector"])
            else:
                await page.press(login_selector.get("password_selector", "body"), "Enter")
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            # Now scrape the target URL
            return await self.scrape_page_async(url, **kwargs)
            
        finally:
            await page.close()
    
    def close(self):
        """Close browser and cleanup resources."""
        if self.context:
            asyncio.run(self.context.close())
            self.context = None
        
        if self.browser:
            asyncio.run(self.browser.close())
            self.browser = None
        
        if self.playwright:
            asyncio.run(self.playwright.stop())
            self.playwright = None

