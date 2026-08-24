"""
AI Job Hunter — HR & Recruiter Email Resolver
Strictly validates recipient addresses to ensure emails are ONLY sent to legitimate employer HR/recruitment contacts.
NEVER sends emails to candidate's own address or job aggregator domains.
"""

import re
import urllib.parse
from typing import Optional, Tuple

# All aggregator domains and candidate domains that must NEVER be used as recipients
BANNED_DOMAINS = {
    "reliefweb.int", "remoteok.com", "remoteok.io", "arbeitnow.com", "arbeitnow.co.uk",
    "devex.com", "hotnigerianjobs.com", "linkedin.com", "indeed.com",
    "glassdoor.com", "monster.com", "ziprecruiter.com", "google.com",
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "example.com", "example-ngo.org"
}

IGNORED_PREFIXES = {
    "noreply", "no-reply", "donotreply", "mailer-daemon", "support", "help",
    "abuse", "postmaster", "feedback", "davidolagbenro"
}


class HREmailResolver:
    @staticmethod
    def resolve_recipient(
        description: str,
        canonical_url: str = "",
        employer: str = ""
    ) -> Tuple[Optional[str], str]:
        """
        Extracts genuine employer HR email.
        Returns: (verified_hr_email or None, method)
        method is 'direct_email' only if a verified external company HR email is found; otherwise 'portal_apply'.
        """
        if not description:
            description = ""

        # 1. Search description for explicit email addresses
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        found_emails = re.findall(email_pattern, description)

        for email in found_emails:
            clean = email.strip().lower()
            if "@" not in clean:
                continue
            prefix, domain = clean.split("@", 1)

            # Reject banned aggregator domains or candidate email
            if any(banned in domain for banned in BANNED_DOMAINS):
                continue
            if any(clean.startswith(p) for p in IGNORED_PREFIXES):
                continue

            # Prioritize recruitment-specific addresses
            if any(k in prefix for k in ["hr", "career", "job", "recruit", "talent", "apply", "hiring", "people"]):
                return clean, "direct_email"

        # If any other valid corporate/NGO domain was found in text
        for email in found_emails:
            clean = email.strip().lower()
            if "@" not in clean:
                continue
            prefix, domain = clean.split("@", 1)
            if not any(banned in domain for banned in BANNED_DOMAINS) and not any(clean.startswith(p) for p in IGNORED_PREFIXES):
                return clean, "direct_email"

        # 2. No direct email found -> strictly a portal application (do NOT invent domain emails)
        return None, "portal_apply"
