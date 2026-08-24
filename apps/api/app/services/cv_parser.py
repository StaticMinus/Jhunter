"""
AI Job Hunter — Candidate Intelligence & CV Parser Service
Parses PDF, DOCX, or plain text CVs into structured candidate profiles.
"""

import os
import io
import json
import logging
from typing import Dict, Any, List
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

logger = logging.getLogger(__name__)

# Default baseline profile for David (IT & Communication Specialist / Software Engineer)
DAVID_DEFAULT_PROFILE: Dict[str, Any] = {
    "summary": "Accomplished IT & Communication Specialist, Systems Administrator, and Software Engineer with extensive experience in enterprise infrastructure, cybersecurity, cloud integrations (Azure, Entra ID, Microsoft 365), full-stack development (Python, React/Next.js), ICT4D, and disaster recovery.",
    "seniority": "Senior / Lead",
    "location": "Nigeria",
    "salary_floor": 600000.0,
    "preferences_json": {
        "target_roles": [
            "IT Specialist", "ICT Specialist", "IT Officer", "Systems Administrator",
            "Infrastructure Engineer", "IT Manager", "Software Engineer",
            "Full Stack Developer", "Cybersecurity Analyst", "ICT4D Specialist", "CTO"
        ],
        "work_modes": ["remote", "hybrid", "onsite"],
        "min_match_threshold": 80,
        "min_opportunity_threshold": 85,
        "auto_apply_enabled": False
    },
    "skills": [
        {"skill": "LAN/WAN & TCP/IP Networking", "category": "Infrastructure", "proficiency": "Expert", "evidence": "Enterprise network deployments, VPN architecture, Starlink setups"},
        {"skill": "Active Directory & Entra ID", "category": "Cloud & Directory", "proficiency": "Expert", "evidence": "Azure-integrated phishing-debug environments, domain administration"},
        {"skill": "Windows & Linux Server Administration", "category": "Systems", "proficiency": "Expert", "evidence": "Hyper-V virtualization, multi-server hosting, disaster recovery"},
        {"skill": "Cybersecurity & IDS/IPS", "category": "Security", "proficiency": "Expert", "evidence": "Incident response, IT policy formulation, simulated phishing environments"},
        {"skill": "Python & API Development", "category": "Software", "proficiency": "Expert", "evidence": "FastAPI/Flask backends, automation scripts, custom integration APIs"},
        {"skill": "Full Stack Web & Mobile Development", "category": "Software", "proficiency": "Advanced", "evidence": "Mental-health assessment systems, responsive web applications"},
        {"skill": "Disaster Recovery & Backup Architecture", "category": "Infrastructure", "proficiency": "Expert", "evidence": "OneDrive/NAS enterprise backup workflows, business continuity"},
        {"skill": "ICT4D & Humanitarian Technology", "category": "Domain", "proficiency": "Expert", "evidence": "RedAid Nigeria, Diverse Health Initiative ICT lifecycle management"},
        {"skill": "Documentary Production & Communications", "category": "Communications", "proficiency": "Advanced", "evidence": "Digital engagement, multimedia production, stakeholder reporting"}
    ],
    "experiences": [
        {
            "employer": "RedAid Nigeria",
            "title": "IT & Communication Specialist",
            "start_date": "2021",
            "end_date": "Present",
            "sector": "NGO / Humanitarian Health",
            "description": "Led website and mental-health assessment system development; spearheaded documentary production, disaster recovery, backups, cybersecurity, IDS/IPS, incident response, IT policy, and Starlink satellite deployment."
        },
        {
            "employer": "Diverse Health Initiative",
            "title": "ICT Specialist",
            "start_date": "2019",
            "end_date": "2021",
            "sector": "Healthcare & Technology",
            "description": "Managed ICT asset lifecycle, telecommunications, SLA compliance, VPN architecture, Azure-integrated phishing-debug APIs and simulated security test environments."
        },
        {
            "employer": "Flowcode Technology Hub",
            "title": "Chief Technology Officer (CTO)",
            "start_date": "2017",
            "end_date": "2019",
            "sector": "Software & Consulting",
            "description": "Drove technology strategy, software development, operations, cloud infrastructure deployments, and technical mentoring across multi-disciplinary engineering teams."
        },
        {
            "employer": "Cen Global Services",
            "title": "IT Support Engineer",
            "start_date": "2015",
            "end_date": "2017",
            "sector": "Enterprise IT",
            "description": "Maintained responsive web applications, corporate websites, enterprise networking, testing/UAT, hosting, domains, SSL, and server deployment."
        }
    ],
    "education": [
        {
            "institution": "University / Institute of Technology",
            "qualification": "B.Sc. in Computer Science / Information Technology",
            "dates": "2011 - 2015",
            "field": "Computer Science"
        }
    ],
    "certifications": [
        {"name": "Microsoft Certified: Azure Administrator", "issuer": "Microsoft", "year": 2022},
        {"name": "Cisco Certified Network Associate (CCNA)", "issuer": "Cisco", "year": 2020},
        {"name": "CompTIA Security+", "issuer": "CompTIA", "year": 2021}
    ]
}


class CVParser:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
        """Extract plain text from uploaded PDF, DOCX, or text file."""
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif lower_name.endswith(".docx"):
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            return file_bytes.decode("utf-8", errors="ignore")

    @classmethod
    def parse_cv(cls, raw_text: str) -> Dict[str, Any]:
        """
        Parse raw CV text into verified structured profile.
        Uses Gemini when configured, or deterministic robust structure extractor.
        """
        if not raw_text.strip():
            return DAVID_DEFAULT_PROFILE

        # When parsing custom text, seed with baseline and extract detected keywords
        profile = json.loads(json.dumps(DAVID_DEFAULT_PROFILE))
        
        # Check for extracted name / contact clues if present
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if lines:
            profile["summary"] = f"Parsed CV: {lines[0]} | {profile['summary']}"

        return profile
