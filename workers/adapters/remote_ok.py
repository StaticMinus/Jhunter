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

    async def search(self, query: str = "", location: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(self.base_url)
                if res.status_code == 200:
                    items = res.json()
                    # Filter out metadata elements
                    jobs = [i for i in items if isinstance(i, dict) and i.get("id")]
                    matches = []
                    q_lower = query.lower() if query else ""
                    for j in jobs:
                        pos = str(j.get("position") or "")
                        desc = str(j.get("description") or "")
                        tags = j.get("tags") or []
                        tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)
                        combined = f"{pos} {tags_str} {desc}".lower()

                        # Disqualify non-IT roles (MEAL, monitoring, pure data analysis)
                        if any(disqualifier in pos.lower() for disqualifier in ["meal", "monitoring and evaluation", "data analyst", "m&e", "biostatistician", "nurse", "accountant", "procurement"]):
                            continue

                        allowed_tech_keywords = [
                            "devops", "sysadmin", "python", "systems", "cloud", "security",
                            "engineer", "infra", "network", "architect", "ai", "developer",
                            "penetration", "cyber", "fellowship", "fellow", "cto", "lead", "ict"
                        ]
                        if q_lower and q_lower not in combined and not any(kw in combined for kw in allowed_tech_keywords):
                            continue

                        matches.append(self.normalize(j))
                        if len(matches) >= 30:
                            break
                    return matches
        except Exception as e:
            print(f"RemoteOK Adapter Error: {e}")
        return []

    async def fetch_job(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        return None

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "external_id": f"remoteok_{raw.get('id', '')}",
            "canonical_url": raw.get("url") or f"https://remoteok.com/l/{raw.get('id', '')}",
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

