import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Optional
import aiohttp

try:
    from config import AppConfig
    from models.job import Job
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.config import AppConfig
    from job_finder.models.job import Job
    from job_finder.utils.logger import get_logger

logger = get_logger()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

class BaseSource(ABC):
    source_name: str = "Base"

    def __init__(self, config: AppConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    def get_random_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_url(self, url: str, headers: Optional[dict] = None, json: bool = False) -> Optional[str | dict]:
        async with self.semaphore:
            h = headers or self.get_random_headers()
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=h, allow_redirects=True) as resp:
                        if resp.status == 200:
                            if json:
                                return await resp.json()
                            return await resp.text()
                        else:
                            logger.warning(f"[{self.source_name}] Request to {url} returned HTTP {resp.status}")
                            return None
            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to fetch {url}: {e}")
                return None

    async def fetch_post(self, url: str, payload: dict, headers: Optional[dict] = None) -> Optional[dict]:
        async with self.semaphore:
            h = headers or self.get_random_headers()
            h["Content-Type"] = "application/json"
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload, headers=h) as resp:
                        if resp.status in (200, 201):
                            return await resp.json()
                        else:
                            logger.warning(f"[{self.source_name}] POST to {url} returned HTTP {resp.status}")
                            return None
            except Exception as e:
                logger.error(f"[{self.source_name}] Failed POST to {url}: {e}")
                return None

    @abstractmethod
    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        pass
