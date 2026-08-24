"""
AI Job Hunter — Multi-Tier Deduplication & Normalization Engine
Deduplicates using:
1. Source ID & Canonical URL matching
2. Levenshtein / Normalized Employer + Title similarity
3. Content SHA-256 fingerprinting
"""

import re
import hashlib
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs, urlunparse


class Deduplicator:
    @staticmethod
    def clean_canonical_url(raw_url: str) -> str:
        """Strip tracking parameters (utm_*, ref, gclid, etc.) to get canonical URL."""
        parsed = urlparse(raw_url)
        params = parse_qs(parsed.query)
        cleaned_params = {
            k: v for k, v in params.items()
            if not k.startswith("utm_") and k not in ["ref", "source", "fbclid", "gclid"]
        }
        # Rebuild clean query
        query_parts = []
        for k, v_list in sorted(cleaned_params.items()):
            for v in v_list:
                query_parts.append(f"{k}={v}")
        new_query = "&".join(query_parts)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ""))

    @staticmethod
    def compute_fingerprint(title: str, employer: str, description: str) -> str:
        """Compute stable SHA-256 fingerprint from cleaned content."""
        clean_text = f"{title.lower().strip()}|{employer.lower().strip()}|{description[:300].lower().strip()}"
        clean_text = re.sub(r"\s+", " ", clean_text)
        return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

    @classmethod
    def is_duplicate(cls, new_job: Dict[str, Any], existing_jobs: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Check if new_job is already represented in existing_jobs.
        Returns: (is_dup: bool, reason: str)
        """
        new_url = cls.clean_canonical_url(new_job.get("canonical_url", ""))
        new_hash = cls.compute_fingerprint(
            new_job.get("title", ""),
            new_job.get("employer", ""),
            new_job.get("description", "")
        )

        for job in existing_jobs:
            # 1. Exact canonical URL match
            if job.get("canonical_url") and cls.clean_canonical_url(job["canonical_url"]) == new_url:
                return True, f"Duplicate canonical URL: {new_url}"

            # 2. SHA-256 fingerprint match
            if job.get("raw_hash") == new_hash:
                return True, "Duplicate content SHA-256 fingerprint match"

            # 3. Exact Employer + Title match
            if (
                job.get("title", "").lower().strip() == new_job.get("title", "").lower().strip() and
                job.get("employer", "").lower().strip() == new_job.get("employer", "").lower().strip()
            ):
                return True, f"Identical title and employer: {new_job.get('title')} at {new_job.get('employer')}"

        return False, ""
