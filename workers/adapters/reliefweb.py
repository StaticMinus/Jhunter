"""
AI Job Hunter — ReliefWeb Live RSS & Deep Page Scraper Adapter
Fetches live worldwide humanitarian & NGO jobs and extracts direct HR application emails.
"""

from typing import List, Dict, Any, Optional
import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class ReliefWebAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="ReliefWeb Global Humanitarian Jobs",
            base_url="https://reliefweb.int/jobs/rss.xml"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(self.base_url)
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    items = root.findall(".//item")
                    jobs = []
                    q_lower = query.lower() if query else ""

                    for item in items:
                        title = item.findtext("title", "").strip()
                        link = item.findtext("link", "").strip()
                        desc = item.findtext("description", "").strip()

                        # Filter by relevant query keywords
                        combined = f"{title} {desc}".lower()
                        if q_lower and q_lower not in combined and not any(kw in combined for kw in ["ict", "it", "systems", "cyber", "technology", "digital", "data", "engineer"]):
                            continue

                        # Deep scrape page for direct HR email
                        direct_email = None
                        try:
                            page_res = await client.get(link, timeout=6.0)
                            if page_res.status_code == 200:
                                emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', page_res.text)
                                valid = [
                                    e for e in set(emails)
                                    if "reliefweb.int" not in e.lower()
                                    and not e.endswith(".png")
                                    and not e.endswith(".jpg")
                                    and not any(e.lower().startswith(p) for p in ["noreply", "no-reply", "support"])
                                ]
                                if valid:
                                    direct_email = valid[0]
                                    desc += f"\n\nDIRECT_APPLICATION_EMAIL: {direct_email}"
                        except Exception:
                            pass

                        raw = {
                            "external_id": f"rw_{abs(hash(link))}",
                            "canonical_url": link,
                            "title": title,
                            "employer": "International Humanitarian Organisation",
                            "location": "Worldwide / International",
                            "work_mode": "remote" if "remote" in combined else "hybrid",
                            "salary_min": None,
                            "salary_max": None,
                            "currency": "USD",
                            "description": desc,
                            "posted_at": datetime.now(timezone.utc).isoformat()
                        }
                        jobs.append(self.normalize(raw))
                        if len(jobs) >= 12:
                            break

                    return jobs
        except Exception as e:
            print(f"ReliefWeb RSS error: {e}")
        return []

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://reliefweb.int"),
            "title": raw.get("title", "ICT Specialist"),
            "employer": raw.get("employer", "International Humanitarian Organisation"),
            "location": raw.get("location", "Worldwide"),
            "work_mode": raw.get("work_mode", "remote"),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "currency": raw.get("currency", "USD"),
            "description": raw.get("description", "Humanitarian IT and systems role."),
            "posted_at": raw.get("posted_at", datetime.now(timezone.utc).isoformat())
        }

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(self.base_url)
                return res.status_code == 200
        except Exception:
            return False
