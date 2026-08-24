"""
AI Job Hunter — WeWorkRemotely Worldwide Tech & Systems Adapter
Fetches the latest live remote programming, DevOps, systems, and security jobs worldwide.
"""

from typing import List, Dict, Any, Optional
import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class WeWorkRemotelyAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="WeWorkRemotely Global Tech Jobs",
            base_url="https://weworkremotely.com/categories"
        )
        self.feed_urls = [
            "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
            "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        ]

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        jobs = []
        q_lower = query.lower() if query else ""

        try:
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                for feed in self.feed_urls:
                    try:
                        res = await client.get(feed)
                        if res.status_code != 200:
                            continue
                        root = ET.fromstring(res.text)
                        items = root.findall(".//item")

                        for item in items:
                            title = item.findtext("title", "").strip()
                            link = item.findtext("link", "").strip()
                            desc = item.findtext("description", "").strip()

                            # Parse employer from title format "Company: Title"
                            employer = "Global Tech Company"
                            role_title = title
                            if ":" in title:
                                parts = title.split(":", 1)
                                employer = parts[0].strip()
                                role_title = parts[1].strip()

                            # Filter relevance
                            combined = f"{role_title} {desc}".lower()
                            if q_lower and q_lower not in combined and not any(kw in combined for kw in ["devops", "sysadmin", "systems", "cloud", "security", "python", "engineer", "network"]):
                                continue

                            # Live deep scrape for direct email on page
                            direct_email = None
                            try:
                                page_res = await client.get(link, timeout=5.0)
                                if page_res.status_code == 200:
                                    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', page_res.text)
                                    valid = [
                                        e for e in set(emails)
                                        if "weworkremotely" not in e.lower()
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
                                "external_id": f"wwr_{abs(hash(link))}",
                                "canonical_url": link,
                                "title": role_title,
                                "employer": employer,
                                "location": "Worldwide / Remote",
                                "work_mode": "remote",
                                "salary_min": None,
                                "salary_max": None,
                                "currency": "USD",
                                "description": desc,
                                "posted_at": datetime.now(timezone.utc).isoformat()
                            }
                            jobs.append(self.normalize(raw))
                            if len(jobs) >= 15:
                                break
                    except Exception as fe:
                        print(f"Error parsing WWR feed {feed}: {fe}")
        except Exception as e:
            print(f"WWR Adapter Error: {e}")

        return jobs

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": str(raw.get("external_id", "")),
            "canonical_url": raw.get("canonical_url", "https://weworkremotely.com"),
            "title": raw.get("title", "Systems Engineer"),
            "employer": raw.get("employer", "Global Tech Company"),
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
