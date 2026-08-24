"""
AI Job Hunter — ReliefWeb (UN & Humanitarian Jobs) Source Adapter
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class ReliefWebAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="ReliefWeb Humanitarian Jobs",
            base_url="https://api.reliefweb.int/v1/jobs"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Structured query against public permitted ReliefWeb API
        params = {
            "appname": "jhunter-recruitment-intelligence",
            "query[value]": f"{query} {location or ''}".strip(),
            "limit": 10,
            "profile": "full"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    raw_items = data.get("data", [])
                    return [self.normalize(item) for item in raw_items]
        except Exception:
            pass
        return []

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{self.base_url}/{url_or_id}")
                if res.status_code == 200:
                    return self.normalize(res.json().get("data", [{}])[0])
        except Exception:
            pass
        return None

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        fields = raw.get("fields", {})
        source_orgs = fields.get("source", [{}])
        employer = source_orgs[0].get("name", "International Organization") if source_orgs else "International Org"
        
        country = fields.get("country", [{}])
        location = country[0].get("name", "Worldwide / International") if country else "Worldwide"

        return {
            "external_id": str(raw.get("id", "")),
            "canonical_url": fields.get("url", f"https://reliefweb.int/job/{raw.get('id', '')}"),
            "title": fields.get("title", "ICT Specialist"),
            "employer": employer,
            "location": location,
            "work_mode": "hybrid" if "hybrid" in fields.get("body", "").lower() else "remote",
            "salary_min": None,
            "salary_max": None,
            "currency": "USD",
            "description": fields.get("body", "Humanitarian IT and telecommunications role."),
            "posted_at": datetime.now(timezone.utc).isoformat()
        }

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("https://api.reliefweb.int/v1/jobs?limit=1")
                return res.status_code == 200
        except Exception:
            return False
