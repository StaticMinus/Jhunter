"""
AI Job Hunter — Devex Global Development Jobs Adapter
Devex covers: NGOs, INGOs, UN agencies, World Bank, USAID, FCDO, EU Aid — all worldwide.
Uses Devex public job search (RSS / public endpoint).
"""

from typing import List, Dict, Any, Optional
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter


class DevexAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="Devex International Development Jobs",
            base_url="https://www.devex.com"
        )

    async def search(self, query: str, location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Devex provides a public RSS feed for job searches worldwide.
        """
        q = query.replace(" ", "+")
        rss_url = f"https://www.devex.com/jobs/search.rss?q={q}&location=&sector=&type="

        try:
            headers = {
                "User-Agent": "JHunter-Recruitment-Agent/1.0 (compatible; job intelligence tool)"
            }
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(rss_url)
                if res.status_code == 200 and "<item>" in res.text:
                    return self._parse_rss(res.text)
        except Exception:
            pass
        return []

    def normalize(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw item or dictionary into standard Jhunter Job schema."""
        return {
            "external_id": str(raw_job.get("external_id", "")),
            "canonical_url": raw_job.get("canonical_url", "https://www.devex.com/jobs"),
            "title": raw_job.get("title", "ICT Specialist"),
            "employer": raw_job.get("employer", "International Organisation"),
            "location": raw_job.get("location", "Worldwide"),
            "work_mode": raw_job.get("work_mode", "remote"),
            "salary_min": raw_job.get("salary_min"),
            "salary_max": raw_job.get("salary_max"),
            "currency": raw_job.get("currency", "USD"),
            "description": raw_job.get("description", "International development technology role."),
            "posted_at": raw_job.get("posted_at", datetime.now(timezone.utc).isoformat())
        }

    def _parse_rss(self, xml_content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            root = ET.fromstring(xml_content)
            channel = root.find("channel")
            if not channel:
                return []
            for item in channel.findall("item")[:15]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                description = item.findtext("description", "").strip()
                pub_date = item.findtext("pubDate", "")
                employer = "International NGO"
                location = "Worldwide"
                if " - " in title:
                    parts = title.split(" - ", 1)
                    title = parts[0].strip()
                    rest = parts[1]
                    if "|" in rest:
                        emp_parts = rest.split("|", 1)
                        employer = emp_parts[0].strip()
                        location = emp_parts[1].strip()
                    else:
                        employer = rest.strip()

                try:
                    posted_at = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").isoformat()
                except Exception:
                    posted_at = datetime.now(timezone.utc).isoformat()

                raw = {
                    "external_id": f"devex_{abs(hash(link))}",
                    "canonical_url": link or "https://www.devex.com/jobs",
                    "title": title,
                    "employer": employer,
                    "location": location,
                    "work_mode": "remote" if "remote" in (title + description).lower() else "on-site",
                    "salary_min": None,
                    "salary_max": None,
                    "currency": "USD",
                    "description": description[:2000] if description else f"International development role: {title}",
                    "posted_at": posted_at
                }
                jobs.append(self.normalize(raw))
        except ET.ParseError:
            pass
        return jobs

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("https://www.devex.com", follow_redirects=True)
                return res.status_code == 200
        except Exception:
            return False
