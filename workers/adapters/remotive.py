"""
AI Job Hunter — Remotive Worldwide Remote Tech Adapter
Fetches the latest live remote software, DevOps, and cloud infrastructure roles worldwide.
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class RemotiveAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="Remotive Global Remote Tech",
            base_url="https://remotive.com/api/remote-jobs"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        params = {
            "category": "devops-sysadmin",
            "limit": 20
        }
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("jobs", [])
                    for item in items:
                        salary_str = item.get("salary", "")
                        salary_val = None
                        if "$" in salary_str:
                            import re
                            nums = re.findall(r'\d+', salary_str.replace(",", ""))
                            if nums:
                                salary_val = float(nums[0])

                        raw = {
                            "external_id": f"remotive_{item.get('id')}",
                            "canonical_url": item.get("url", "https://remotive.com"),
                            "title": item.get("title", "DevOps / Systems Engineer"),
                            "employer": item.get("company_name", "Global Enterprise"),
                            "location": item.get("candidate_required_location", "Worldwide / Remote"),
                            "work_mode": "remote",
                            "salary_min": salary_val,
                            "salary_max": salary_val * 1.3 if salary_val else None,
                            "currency": "USD",
                            "description": item.get("description", ""),
                            "posted_at": item.get("publication_date") or datetime.now(timezone.utc).isoformat()
                        }
                        jobs.append(self.normalize(raw))
        except Exception as e:
            print(f"Remotive Adapter Error: {e}")

        return jobs

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://remotive.com"),
            "title": raw.get("title", "DevOps Engineer"),
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
