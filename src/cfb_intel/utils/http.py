"""Polite HTTP client with retries, delay, and filesystem cache."""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from cfb_intel.config import RAW_DIR, settings
from cfb_intel.utils.rate_limit import RateLimiter

LOGGER = logging.getLogger(__name__)


@dataclass
class HttpResult:
    url: str
    status_code: int
    text: str
    from_cache: bool = False


class PoliteHttpClient:
    def __init__(
        self,
        user_agent: str | None = None,
        delay_seconds: float | None = None,
        cache_dir: Path | None = None,
        timeout: int = 20,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent or settings.user_agent})
        self.timeout = timeout
        self.cache_dir = cache_dir or RAW_DIR / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limiter = RateLimiter(settings.request_delay_seconds if delay_seconds is None else delay_seconds)
        self._robots_cache: dict[str, RobotFileParser] = {}

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.txt"

    def get(self, url: str, *, use_cache: bool = True, retries: int = 2) -> HttpResult | None:
        cache_path = self._cache_path(url)
        if use_cache and cache_path.exists():
            return HttpResult(url=url, status_code=200, text=cache_path.read_text(encoding="utf-8"), from_cache=True)

        for attempt in range(retries + 1):
            try:
                self.rate_limiter.wait()
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code in {403, 429}:
                    LOGGER.warning("source declined request", extra={"cfb_url": url, "cfb_status": response.status_code})
                    return HttpResult(url=url, status_code=response.status_code, text=response.text)
                if response.status_code == 404:
                    LOGGER.info("source has no record", extra={"cfb_url": url, "cfb_status": response.status_code})
                    return HttpResult(url=url, status_code=response.status_code, text=response.text)
                response.raise_for_status()
                cache_path.write_text(response.text, encoding="utf-8")
                return HttpResult(url=url, status_code=response.status_code, text=response.text)
            except requests.RequestException as exc:
                if attempt >= retries:
                    LOGGER.warning("http request failed", extra={"cfb_url": url, "cfb_error": str(exc)})
                    return None
                time.sleep(2**attempt)
        return None

    def allowed_by_robots(self, url: str) -> bool:
        """Check robots.txt for HTML scraping adapters.

        JSON/API adapters may have separate terms and endpoint rules, so this
        helper is opt-in instead of globally blocking all requests.
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            robot = RobotFileParser()
            robot.set_url(f"{base}/robots.txt")
            try:
                robot.read()
            except Exception as exc:
                LOGGER.warning("robots.txt read failed", extra={"cfb_url": url, "cfb_error": str(exc)})
                return False
            self._robots_cache[base] = robot
        return self._robots_cache[base].can_fetch(self.session.headers["User-Agent"], url)
