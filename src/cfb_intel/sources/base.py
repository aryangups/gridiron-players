"""Base interface for pluggable data sources."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from cfb_intel.config import settings

LOGGER = logging.getLogger(__name__)


class Source(ABC):
    source_name: str = "base"
    source_url: str = ""
    rate_limit_seconds: float = settings.request_delay_seconds
    enabled: bool = True
    kind: str = "generic"

    @abstractmethod
    def fetch(self) -> Any:
        """Fetch raw source data."""

    @abstractmethod
    def parse(self, raw: Any) -> Any:
        """Parse fetched source data."""

    @abstractmethod
    def normalize(self, parsed: Any) -> dict[str, list[Any]]:
        """Convert parsed data into normalized pipeline records."""

    def run(self) -> dict[str, list[Any]]:
        if not self.enabled:
            LOGGER.info("source skipped", extra={"cfb_source": self.source_name, "cfb_reason": "disabled"})
            return {}
        try:
            return self.normalize(self.parse(self.fetch()))
        except Exception as exc:
            LOGGER.warning("source failed", extra={"cfb_source": self.source_name, "cfb_error": str(exc)}, exc_info=True)
            return {}

