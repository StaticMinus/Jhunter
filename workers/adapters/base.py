"""
AI Job Hunter — Job Source Connector Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class JobSourceAdapter(ABC):
    """
    Abstract connector interface for all job boards, RSS feeds, and APIs.
    """

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url

    @abstractmethod
    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search jobs matching query and location."""
        pass

    @abstractmethod
    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full job detail description."""
        pass

    @abstractmethod
    def normalize(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw payload into standard Jhunter Job schema."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source endpoint is reachable and responsive."""
        pass
