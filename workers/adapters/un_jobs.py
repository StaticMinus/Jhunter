"""
AI Job Hunter — UN Jobs / UNDP / WHO / UNICEF Job Board Adapter
Free public API: https://unjobs.org & reliefweb UN agency filter
Covers: UN system, World Bank, WHO, UNDP, UNICEF, IOM, WFP — all worldwide.
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class UNJobsAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="UN & International Org Jobs",
            base_url="https://api.reliefweb.int/v1/jobs"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search ReliefWeb filtered to UN system organisations only.
        ReliefWeb's API lets us filter by source (UN agencies, World Bank, etc.)
        """
        params = {
            "appname": "jhunter-recruitment-intelligence",
            "query[value]": query,
            "sort[]": "date.created:desc",
            "limit": 20,
            "profile": "full",
            # Filter to UN / international organisations only
            "filter[field]": "source.type",
            "filter[value][]": ["International Organization", "UN Organization"]
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    raw_items = data.get("data", [])
                    return [self.normalize(item) for item in raw_items if item]
        except Exception:
            pass
        return []

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        fields = raw.get("fields", {})
        source_orgs = fields.get("source", [{}])
        employer = source_orgs[0].get("name", "UN System Agency") if source_orgs else "International Organisation"

        country = fields.get("country", [{}])
        if country:
            location = country[0].get("name", "Worldwide")
        else:
            location = "Worldwide / Remote"

        date_created = fields.get("date", {}).get("created") or datetime.now(timezone.utc).isoformat()
        canonical_url = fields.get("url") or f"https://reliefweb.int/job/{raw.get('id', '')}"

        body = fields.get("body", "")
        # Determine work mode from description
        if "remote" in body.lower():
            work_mode = "remote"
        elif "hybrid" in body.lower():
            work_mode = "hybrid"
        else:
            work_mode = "on-site"

        return {
            "external_id": f"un_{raw.get('id', '')}",
            "canonical_url": canonical_url,
            "title": fields.get("title", "ICT/IT Specialist"),
            "employer": employer,
            "location": location,
            "work_mode": work_mode,
            "salary_min": None,
            "salary_max": None,
            "currency": "USD",
            "description": body or "International organisation technical role.",
            "posted_at": date_created
        }

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("https://api.reliefweb.int/v1/jobs?limit=1")
                return res.status_code == 200
        except Exception:
            return False
