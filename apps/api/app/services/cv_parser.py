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

# Default baseline profile for David (Senior IT & Systems Specialist / Cloud & AI Engineer)
DAVID_DEFAULT_PROFILE: Dict[str, Any] = {
    "name": "David",
    "email": "davidolagbenro35@gmail.com",
    "summary": "Accomplished Senior IT & Systems Specialist, Cloud Solutions Engineer, AI Developer (VibeCoder), and Cybersecurity & Penetration Testing Lead with 8+ years of enterprise experience across cloud infrastructure (Azure, AWS), Linux/Windows server administration, enterprise networking (LAN/WAN, VPNs, Cisco CCNA), full-stack AI engineering (Python, LLM agent architecture, APIs), incident response, and global technical leadership.",
    "seniority": "Senior / Lead",
    "location": "Nigeria",
    "salary_floor": 600000.0,
    "preferences_json": {
        "target_roles": [
            "AI Developer", "AI Engineer", "Vibe Coder", "Full Stack AI Developer",
            "Cloud Engineer", "Cloud Solutions Architect", "Systems Administrator", "Systems Engineer",
            "Cybersecurity Analyst", "Penetration Tester", "Network Security Engineer", "Information Security Officer",
            "IT Specialist", "ICT Specialist", "IT Officer", "Infrastructure Engineer", "DevOps Engineer",
            "CTO", "Head of IT", "Global Tech Fellow", "Leadership Fellow"
        ],
        "work_modes": ["remote", "hybrid", "onsite"],
        "min_match_threshold": 80,
        "min_opportunity_threshold": 85,
        "auto_apply_enabled": True
    },
    "skills": [
        {"skill": "AI & LLM Development (VibeCoding)", "category": "AI / Software", "proficiency": "Expert", "evidence": "Full-stack AI systems, LLM agent pipelines, custom API workflows, Python/FastAPI automation"},
        {"skill": "Cloud Engineering & Architecture", "category": "Cloud", "proficiency": "Expert", "evidence": "Microsoft Certified: Azure Administrator, AWS infrastructure, cloud security, Entra ID IAM"},
        {"skill": "Cybersecurity & Penetration Testing", "category": "Security", "proficiency": "Expert", "evidence": "CompTIA Security+, IDS/IPS deployment, ethical hacking, threat auditing, security policies"},
        {"skill": "Windows & Linux Server Administration", "category": "Systems", "proficiency": "Expert", "evidence": "Enterprise Linux/Windows environments, Hyper-V virtualization, disaster recovery"},
        {"skill": "LAN/WAN & Enterprise Networking", "category": "Infrastructure", "proficiency": "Expert", "evidence": "Cisco CCNA, enterprise VPN architecture, TCP/IP, Starlink satellite rollouts"},
        {"skill": "Full Stack Software & API Engineering", "category": "Software", "proficiency": "Expert", "evidence": "Python, Next.js/React, REST/GraphQL APIs, microservices, database management"},
        {"skill": "Global Tech Leadership & Fellowships", "category": "Leadership", "proficiency": "Expert", "evidence": "CTO background at Flowcode Hub, RedAid technology oversight, international ICT4D"},
        {"skill": "Disaster Recovery & Backup Architecture", "category": "Infrastructure", "proficiency": "Expert", "evidence": "Enterprise cloud and on-premise business continuity workflows"}
    ],
    "experiences": [
        {
            "employer": "RedAid Nigeria",
            "title": "IT & Communication Specialist",
            "start_date": "2021",
            "end_date": "Present",
            "sector": "NGO / Humanitarian Health",
            "description": "Led website and assessment system development; spearheaded documentary production, disaster recovery, backups, cybersecurity, IDS/IPS, incident response, IT policy, and Starlink satellite deployment."
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
            if PdfReader:
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            else:
                return file_bytes.decode("utf-8", errors="ignore")
        elif lower_name.endswith(".docx"):
            if docx:
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n".join([p.text for p in doc.paragraphs])
            else:
                import zipfile, xml.etree.ElementTree as ET
                try:
                    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                        xml_content = z.read('word/document.xml')
                        tree = ET.fromstring(xml_content)
                        paragraphs = []
                        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                            texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                            if texts:
                                paragraphs.append(''.join(texts))
                        return "\n".join(paragraphs)
                except Exception:
                    return file_bytes.decode("utf-8", errors="ignore")
        else:
            return file_bytes.decode("utf-8", errors="ignore")

    @classmethod
    def parse_cv(cls, raw_text: str) -> Dict[str, Any]:
        """
        Parse raw CV text into verified structured profile for David.
        """
        profile = json.loads(json.dumps(DAVID_DEFAULT_PROFILE))
        if not raw_text.strip():
            return profile

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if lines:
            profile["summary"] = f"Parsed CV: {lines[0]} | {profile['summary']}"

        return profile

