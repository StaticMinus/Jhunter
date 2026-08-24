"""
AI Job Hunter — Visa Sponsorship & Relocation Detection Utility
"""

import re
from typing import Tuple, List

POSITIVE_VISA_PATTERNS = [
    r"visa\s+sponsorship",
    r"sponsorship\s+available",
    r"will\s+sponsor",
    r"we\s+sponsor",
    r"visa\s+provided",
    r"work\s+permit\s+(support|provided|available)",
    r"relocation\s+(assistance|package|support|provided|allowance|bonus)",
    r"international\s+relocation",
    r"tier\s*2\s+sponsor",
    r"skilled\s+worker\s+visa",
    r"relocation\s+offered",
    r"visa\s+support",
]

NEGATIVE_VISA_PATTERNS = [
    r"no\s+visa\s+sponsorship",
    r"without\s+sponsorship",
    r"unable\s+to\s+sponsor",
    r"cannot\s+sponsor",
    r"not\s+offering\s+sponsorship",
    r"must\s+be\s+authorized\s+to\s+work",
    r"must\s+have\s+existing\s+right\s+to\s+work",
    r"us\s+citizens\s+only",
    r"uk\s+citizens\s+only",
    r"eu\s+citizens\s+only",
    r"no\s+sponsorship\s+available",
]


class VisaDetector:
    """Detects whether a job offers or excludes visa sponsorship."""

    @staticmethod
    def evaluate(title: str, description: str, employer: str = "") -> Tuple[str, List[str]]:
        """
        Returns:
            (visa_signal: str, reasons: List[str])
            visa_signal is one of: 'indicated', 'possible', 'unknown', 'no_indication'
        """
        combined_text = f"{title} {description} {employer}".lower()

        # Check negative patterns first
        for pat in NEGATIVE_VISA_PATTERNS:
            if re.search(pat, combined_text):
                return "no_indication", ["Explicitly states no visa sponsorship available"]

        # Check positive patterns
        found_reasons = []
        for pat in POSITIVE_VISA_PATTERNS:
            match = re.search(pat, combined_text)
            if match:
                found_reasons.append(f"Matched: '{match.group(0)}'")

        if found_reasons:
            return "indicated", found_reasons

        # International organizations / UN system automatically provide visa sponsorship
        un_orgs = [
            "united nations", "undp", "unicef", "who", "unhcr", "wfp", "iom",
            "world bank", "unesco", "fao", "international organization"
        ]
        if any(org in combined_text for org in un_orgs):
            return "indicated", ["UN system / International Organisation provides diplomatic / international work authorization"]

        # Remote international positions provide global compensation without local visa constraint
        if "remote" in combined_text or "worldwide" in combined_text:
            return "possible", ["Worldwide remote arrangement — no local visa constraint required"]

        return "unknown", ["Visa sponsorship not explicitly indicated"]
