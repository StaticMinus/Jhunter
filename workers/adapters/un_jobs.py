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
            base_url="https://reliefweb.int/jobs/rss.xml"
        )

    async def search(self, query: str = "ICT", location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import xml.etree.ElementTree as ET
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        jobs = []
        q_enc = query.replace(" ", "+") if query else "ICT"
        rss_url = f"{self.base_url}?search={q_enc}"

        try:
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(rss_url)
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    items = root.findall(".//item")
                    for item in items:
                        title = item.findtext("title", "").strip()
                        link = item.findtext("link", "").strip()
                        desc = item.findtext("description", "").strip()
                        pub_date = item.findtext("pubDate", "")

                        # Extract employer from title or description
                        employer = "UN Agency / International NGO"
                        if " - " in title:
                            parts = title.split(" - ")
                            if len(parts) >= 2:
                                employer = parts[-1].strip()

                        raw = {
                            "external_id": f"un_{abs(hash(link))}",
                            "canonical_url": link or "https://reliefweb.int",
                            "title": title,
                            "employer": employer,
                            "location": "Worldwide / International",
                            "work_mode": "remote" if "remote" in (title + desc).lower() else "hybrid",
                            "salary_min": None,
                            "salary_max": None,
                            "currency": "USD",
                            "description": desc or "UN and international development technical role.",
                            "posted_at": pub_date or datetime.now(timezone.utc).isoformat()
                        }
                        jobs.append(self.normalize(raw))
                        if len(jobs) >= 25:
                            break
        except Exception as e:
            print(f"UNJobs Adapter Error: {e}")

        return jobs

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://reliefweb.int"),
            "title": raw.get("title", "ICT Specialist"),
            "employer": raw.get("employer", "UN System Agency"),
            "location": raw.get("location", "Worldwide"),
            "work_mode": raw.get("work_mode", "remote"),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "currency": raw.get("currency", "USD"),
            "description": raw.get("description", "UN System / International organisation technical role."),
            "posted_at": raw.get("posted_at", datetime.now(timezone.utc).isoformat())
        }

    async def health_check(self) -> bool:
        return True

