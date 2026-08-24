"""
AI Job Hunter — RemoteOK Public Feed Adapter
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class RemoteOKAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="RemoteOK Global Jobs",
            base_url="https://remoteok.com/api"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {"User-Agent": "Jhunter-Recruitment-Bot/1.0"}
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                res = await client.get(self.base_url)
                if res.status_code == 200:
                    items = res.json()
                    # First element is usually legal/metadata
                    jobs = [i for i in items if isinstance(i, dict) and i.get("id")]
                    matches = []
                    q_lower = query.lower()
                    for j in jobs:
                        text = (j.get("position", "") + j.get("tags", "") + j.get("description", "")).lower()
                        if q_lower in text:
                            matches.append(self.normalize(j))
                            if len(matches) >= 10:
                                break
                    return matches
        except Exception:
            pass
        return []

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("id", "")),
            "canonical_url": raw.get("url", f"https://remoteok.com/l/{raw.get('id', '')}"),
            "title": raw.get("position", "Software Engineer"),
            "employer": raw.get("company", "Remote Company"),
            "location": raw.get("location") or "Worldwide / Remote",
            "work_mode": "remote",
            "salary_min": float(raw.get("salary_min")) if raw.get("salary_min") else None,
            "salary_max": float(raw.get("salary_max")) if raw.get("salary_max") else None,
            "currency": "USD",
            "description": raw.get("description", "Remote software/systems role."),
            "posted_at": datetime.now(timezone.utc).isoformat()
        }

    async def health_check(self) -> bool:
        return True
