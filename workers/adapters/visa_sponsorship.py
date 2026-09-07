"""
AI Job Hunter — Visa Sponsorship & Relocation Tech Jobs Adapter
Fetches roles specifically tagged with Visa Sponsorship, Relocation Assistance across Europe, UK, and Global hubs.
Uses the Arbeitnow Job Board API (visa_sponsorship parameter + EU/UK tech roles).
"""

from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from workers.adapters.base import JobSourceAdapter
from workers.visa_detector import VisaDetector


class VisaSponsorshipAdapter(JobSourceAdapter):
    def __init__(self):
        super().__init__(
            name="Global Visa Sponsorship & Relocation Board",
            base_url="https://www.arbeitnow.com/api/job-board-api"
        )

    async def search(self, query: str = "", location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetches technology and systems jobs with Visa Sponsorship and Relocation support across multiple pages.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        matches = []
        q_lower = query.lower() if query else ""
        pages = filters.get("pages", [1, 2, 3]) if filters else [1, 2, 3]

        try:
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                for page in pages:
                    try:
                        url = f"{self.base_url}?page={page}"
                        res = await client.get(url)
                        if res.status_code != 200:
                            continue
                        data = res.json().get("data", [])
                        for item in data:
                            title = item.get("title", "")
                            desc = item.get("description", "")
                            company = item.get("company_name", "")
                            is_visa_tagged = item.get("visa_sponsorship") is True

                            visa_signal, _ = VisaDetector.evaluate(title, desc, company)
                            if is_visa_tagged:
                                visa_signal = "indicated"

                            combined = f"{title} {desc} {company}".lower()
                            if q_lower and q_lower not in combined:
                                # Keep high-value tech/infrastructure roles
                                if not any(kw in combined for kw in ["devops", "sysadmin", "systems", "cloud", "security", "python", "engineer", "network", "architect", "support", "it"]):
                                    continue

                            if is_visa_tagged or visa_signal in ("indicated", "possible") or any(kw in combined for kw in ["visa", "relocation", "sponsor", "remote"]):
                                matches.append(self.normalize(item))
                                if len(matches) >= 60:
                                    break
                        if len(matches) >= 60:
                            break
                    except Exception as pe:
                        print(f"Visa adapter page {page} error: {pe}")
        except Exception as e:
            print(f"VisaSponsorship Adapter Error: {e}")

        return matches


    def normalize(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw payload into standard Jhunter Job schema."""
        title = raw_job.get("title", "Senior Systems / IT Specialist")
        company = raw_job.get("company_name", "Global Enterprise")
        loc = raw_job.get("location") or "Europe / Worldwide (Visa Sponsored)"
        is_remote = raw_job.get("remote", False)

        return {
            "external_id": f"visa_{raw_job.get('slug', abs(hash(raw_job.get('url', ''))))}",
            "canonical_url": raw_job.get("url", "https://www.arbeitnow.com"),
            "title": title,
            "employer": company,
            "location": loc,
            "work_mode": "remote" if is_remote else "hybrid",
            "salary_min": None,
            "salary_max": None,
            "currency": "EUR",
            "description": raw_job.get("description", "Technology role with visa sponsorship & relocation assistance."),
            "posted_at": datetime.fromtimestamp(raw_job.get("created_at", int(datetime.now(timezone.utc).timestamp())), tz=timezone.utc).isoformat() if isinstance(raw_job.get("created_at"), (int, float)) else datetime.now(timezone.utc).isoformat()
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
