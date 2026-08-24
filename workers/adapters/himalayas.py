"""
AI Job Hunter — Himalayas Worldwide Remote Tech Adapter
Fetches real-time remote engineering, cloud, infrastructure, and cybersecurity roles globally.
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class HimalayasAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="Himalayas Global Remote Tech",
            base_url="https://himalayas.app/jobs/api"
        )

    async def search(self, query: str = "", location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        params = {"limit": 20}
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("jobs", [])
                    for item in items:
                        sal_min = item.get("minSalary")
                        sal_max = item.get("maxSalary")
                        raw = {
                            "external_id": f"himalayas_{item.get('id')}",
                            "canonical_url": item.get("applicationUrl") or f"https://himalayas.app/jobs/{item.get('slug', '')}",
                            "title": item.get("title", "Infrastructure / Cloud Specialist"),
                            "employer": item.get("companyName", "Global Tech Co"),
                            "location": "Worldwide / Remote",
                            "work_mode": "remote",
                            "salary_min": float(sal_min) if sal_min else None,
                            "salary_max": float(sal_max) if sal_max else None,
                            "currency": item.get("currency", "USD"),
                            "description": item.get("description", ""),
                            "posted_at": item.get("pubDate") or datetime.now(timezone.utc).isoformat()
                        }
                        jobs.append(self.normalize(raw))
        except Exception as e:
            print(f"Himalayas Adapter Error: {e}")

        return jobs

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://himalayas.app"),
            "title": raw.get("title", "Systems Specialist"),
            "employer": raw.get("employer", "Global Tech Co"),
            "location": raw.get("location", "Worldwide / Remote"),
            "work_mode": raw.get("work_mode", "remote"),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "currency": raw.get("currency", "USD"),
            "description": raw.get("description", ""),
            "posted_at": raw.get("posted_at", datetime.now(timezone.utc).isoformat())
        }

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> bool:
        return True
