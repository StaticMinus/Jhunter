"""
AI Job Hunter — HR & Recruiter Email Resolver
Extracts and resolves genuine recruiter / HR contact emails from job descriptions and employer domains.
Filters out generic platform scrapers and noreply addresses.
"""

import re
import urllib.parse
from typing import Optional, Tuple

IGNORED_DOMAINS = {
    "reliefweb.int", "remoteok.com", "remoteok.io", "arbeitnow.com",
    "devex.com", "hotnigerianjobs.com", "linkedin.com", "indeed.com",
    "glassdoor.com", "monster.com", "ziprecruiter.com", "google.com",
    "example.com", "example-ngo.org"
}

IGNORED_PREFIXES = {
    "noreply", "no-reply", "donotreply", "mailer-daemon", "support", "help",
    "abuse", "postmaster", "admin@reliefweb.int", "feedback"
}


class HREmailResolver:
    @staticmethod
    def resolve_recipient(
        description: str,
        canonical_url: str = "",
        employer: str = ""
    ) -> Tuple[Optional[str], str]:
        """
        Returns (recipient_email, method)
        method is either 'direct_email' or 'portal_apply'
        """
        if not description:
            description = ""

        # 1. Regex search for explicit email addresses in the job description
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        found_emails = re.findall(email_pattern, description)

        for email in found_emails:
            clean_email = email.strip().lower()
            domain = clean_email.split("@")[-1]
            prefix = clean_email.split("@")[0]

            if domain in IGNORED_DOMAINS:
                continue
            if any(clean_email.startswith(p) for p in IGNORED_PREFIXES):
                continue

            # Prioritize recruitment-specific prefixes
            if any(k in prefix for k in ["hr", "career", "job", "recruit", "talent", "apply", "hiring", "people"]):
                return clean_email, "direct_email"

        # If any other valid non-platform email was found in the text
        for email in found_emails:
            clean_email = email.strip().lower()
            domain = clean_email.split("@")[-1]
            if domain not in IGNORED_DOMAINS and not any(clean_email.startswith(p) for p in IGNORED_PREFIXES):
                return clean_email, "direct_email"

        # 2. Extract company domain from canonical URL if it's a direct employer site
        if canonical_url:
            try:
                parsed = urllib.parse.urlparse(canonical_url)
                netloc = parsed.netloc.lower()
                if netloc.startswith("www."):
                    netloc = netloc[4:]
                if netloc and netloc not in IGNORED_DOMAINS and "." in netloc:
                    # Construct likely HR intake address for direct employer domains
                    hr_email = f"careers@{netloc}"
                    return hr_email, "direct_email"
            except Exception:
                pass

        # 3. If no email is available, it's a web application portal
        return None, "portal_apply"
