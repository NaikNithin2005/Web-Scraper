"""
Anti-Block Engine
Handles user-agent rotation, proxy rotation, captcha solving, and human behavior simulation.
"""

import random
import time
from typing import Dict, List, Optional
from loguru import logger


class AntiBlockEngine:
    """Anti-bot protection bypass engine."""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        captcha_solver: Optional[Any] = None,
        enable_rotation: bool = True
    ):
        self.proxies = proxies or []
        self.current_proxy_index = 0
        self.captcha_solver = captcha_solver
        self.enable_rotation = enable_rotation
        self.request_count = 0
        self.last_request_time = 0
        
    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers with user-agent rotation."""
        user_agent = random.choice(self.USER_AGENTS) if self.enable_rotation else self.USER_AGENTS[0]
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        
        return headers
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation."""
        if not self.proxies:
            return None
        
        if self.enable_rotation:
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        else:
            proxy = self.proxies[0]
        
        # Parse proxy format: http://user:pass@host:port or http://host:port
        if "@" in proxy:
            return {"http": proxy, "https": proxy}
        else:
            return {"http": proxy, "https": proxy}
    
    def wait_before_retry(self, attempt: int, base_delay: float = 1.0):
        """Wait with exponential backoff before retry."""
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
        logger.info(f"Waiting {delay:.2f}s before retry {attempt + 1}")
        time.sleep(delay)
    
    def human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Simulate human-like delay between requests."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def rate_limit_check(self, max_requests_per_minute: int = 30):
        """Check and enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < (60 / max_requests_per_minute):
            wait_time = (60 / max_requests_per_minute) - time_since_last
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
    
    def solve_captcha(self, captcha_data: Any) -> Optional[str]:
        """Solve captcha using integrated solver."""
        if not self.captcha_solver:
            logger.warning("No captcha solver configured")
            return None
        
        try:
            solution = self.captcha_solver.solve(captcha_data)
            return solution
        except Exception as e:
            logger.error(f"Captcha solving failed: {e}")
            return None
    
    def add_proxy(self, proxy: str):
        """Add a proxy to the rotation."""
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy}")
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy from rotation."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"Removed proxy: {proxy}")

