"""
AI Job Hunter — Jobicy Global Remote Tech Adapter
Fetches live remote DevOps, Sysadmin, Cloud, and Cybersecurity jobs worldwide.
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class JobicyAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="Jobicy Global Remote Tech",
            base_url="https://jobicy.com/api/v2/remote-jobs"
        )
        self.tags = ["devops", "security", "sysadmin", "cloud", "python"]

    async def search(self, query: str = "devops", location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        tag = query if query in self.tags else "devops"
        params = {"count": 20, "tag": tag}
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("jobs", [])
                    for item in items:
                        sal_min = item.get("annualSalaryMin")
                        sal_max = item.get("annualSalaryMax")
                        raw = {
                            "external_id": f"jobicy_{item.get('id')}",
                            "canonical_url": item.get("url", "https://jobicy.com"),
                            "title": item.get("jobTitle", "Systems / Cloud Engineer"),
                            "employer": item.get("companyName", "Global Enterprise"),
                            "location": item.get("jobGeo", "Worldwide / Remote"),
                            "work_mode": "remote",
                            "salary_min": float(sal_min) if sal_min else None,
                            "salary_max": float(sal_max) if sal_max else None,
                            "currency": item.get("salaryCurrency", "USD"),
                            "description": item.get("jobDescription", ""),
                            "posted_at": item.get("pubDate") or datetime.now(timezone.utc).isoformat()
                        }
                        jobs.append(self.normalize(raw))
        except Exception as e:
            print(f"Jobicy Adapter Error: {e}")

        return jobs

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://jobicy.com"),
            "title": raw.get("title", "Systems Engineer"),
            "employer": raw.get("employer", "Global Enterprise"),
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
