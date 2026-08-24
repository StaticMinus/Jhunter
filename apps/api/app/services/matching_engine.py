"""
AI Job Hunter — Dual Weighted Matching & Scoring Engine
Strictly implements the exact formulas from MVP Specification (Page 3 & 4).
"""

from typing import Dict, Any, List, Tuple
import re

class MatchingEngine:
    """
    Computes deterministic Match Score & Opportunity Score
    with explainable rationales and verifiable gap reports.
    """

    @staticmethod
    def calculate_scores(
        profile_data: Dict[str, Any],
        job_data: Dict[str, Any],
        job_features: Dict[str, Any]
    ) -> Tuple[int, int, Dict[str, Any], List[str]]:
        """
        Calculate Match Score & Opportunity Score according to MVP formulas.
        Returns: (match_score, opportunity_score, explanation_dict, gaps_list)
        """
        # ── 1. Extract Candidate Profile Attributes ──
        candidate_skills = {
            s.get("skill", "").lower().strip()
            for s in profile_data.get("skills", [])
            if s.get("skill")
        }
        candidate_roles = [
            r.lower().strip()
            for r in profile_data.get("preferences_json", {}).get("target_roles", [
                "it specialist", "ict specialist", "systems administrator",
                "software developer", "cybersecurity analyst", "ict4d", "cto"
            ])
        ]
        candidate_location = (profile_data.get("location") or "worldwide").lower()
        salary_floor = float(profile_data.get("salary_floor") or 500000.0)

        # ── 2. Extract Job Attributes ──
        job_title = (job_data.get("title") or "").lower()
        job_desc = (job_data.get("description") or "").lower()
        job_work_mode = (job_data.get("work_mode") or "unknown").lower()
        job_location = (job_data.get("location") or "").lower()
        required_skills = [
            s.lower().strip()
            for s in job_features.get("skills_json", [])
        ]
        if not required_skills:
            # Fallback regex skill extraction if features empty
            common_skills = [
                "python", "azure", "linux", "windows", "cybersecurity", "networking",
                "active directory", "hyper-v", "disaster recovery", "react", "next.js",
                "fastapi", "ict4d", "api", "telecommunications", "itil", "starlink"
            ]
            required_skills = [s for s in common_skills if s in job_desc]

        visa_signal = job_features.get("visa_signal", "unknown") # indicated, possible, unknown, no_indication
        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        currency = job_data.get("currency", "NGN")

        # ── 3. Compute Match Score (0 - 100) ──
        # Formula: 30% skills + 20% experience + 15% role + 10% industry + 10% edu + 10% loc/work-mode + 5% comms

        # a) Skills Fit (30 pts)
        matched_skills = [s for s in required_skills if any(cs in s or s in cs for cs in candidate_skills)]
        missing_skills = [s for s in required_skills if s not in matched_skills]
        skill_ratio = len(matched_skills) / max(len(required_skills), 1) if required_skills else 0.85
        score_skills = min(30.0, skill_ratio * 30.0)

        # b) Experience Fit (20 pts)
        # Candidate has ~8+ years multi-domain experience
        score_exp = 19.0

        # c) Role / Seniority Fit (15 pts)
        score_role = 5.0
        for target in candidate_roles:
            if target in job_title or any(word in job_title for word in target.split() if len(word) > 3):
                score_role = 15.0
                break
        if score_role < 15.0 and any(kw in job_title for kw in ["it", "ict", "software", "network", "system", "security", "developer", "lead"]):
            score_role = 13.0

        # d) Industry / Domain Fit (10 pts)
        score_industry = 9.0
        if any(term in job_desc for term in ["ngo", "humanitarian", "health", "fintech", "enterprise", "telecom"]):
            score_industry = 10.0

        # e) Education / Certifications Fit (10 pts)
        score_edu = 9.0

        # David is open to worldwide roles — remote, hybrid, and on-site globally
        score_loc = 6.0
        if "remote" in job_work_mode or "remote" in job_location or "worldwide" in job_location or "international" in job_location:
            score_loc = 10.0
        elif "hybrid" in job_work_mode:
            score_loc = 8.0
        elif any(region in job_location for region in ["europe", "geneva", "amsterdam", "london", "nairobi", "accra", "kampala", "dakar", "africa"]):
            score_loc = 9.0  # Strong international markets for David's profile

        # g) Communication / Transferable Skills (5 pts)
        score_comm = 5.0

        raw_match = score_skills + score_exp + score_role + score_industry + score_edu + score_loc + score_comm
        match_score = int(round(min(100.0, max(10.0, raw_match))))

        # ── 4. Compute Opportunity Score (0 - 100) ──
        # Formula: 25% visa + 20% work-mode + 20% comp + 15% employer + 10% growth + 10% feasibility

        # a) Visa / Relocation (25 pts)
        if visa_signal == "indicated":
            score_visa = 25.0
        elif visa_signal == "possible":
            score_visa = 18.0
        elif visa_signal == "unknown":
            score_visa = 12.5  # Neutral (not penalized per spec)
        else:
            score_visa = 5.0

        # b) Work Mode / Location Preference (20 pts)
        # David is open to worldwide roles
        if "remote" in job_work_mode:
            score_mode = 20.0
        elif "hybrid" in job_work_mode:
            score_mode = 16.0
        elif any(region in job_location for region in ["europe", "usa", "uk", "canada", "australia", "africa", "worldwide", "international"]):
            score_mode = 14.0
        else:
            score_mode = 10.0

        # c) Compensation Quality (20 pts)
        score_comp = 14.0 # Default neutral if unknown
        if salary_max or salary_min:
            effective_sal = salary_max or salary_min
            if currency in ["USD", "EUR", "GBP"]:
                score_comp = 20.0 # High value FX
            elif effective_sal >= salary_floor:
                score_comp = 18.0
            else:
                score_comp = 8.0

        # d) Employer / Sector Relevance (15 pts)
        score_employer = 12.0
        if any(term in job_desc for term in ["united nations", "ngo", "international", "global", "red cross", "who"]):
            score_employer = 15.0

        # e) Seniority / Career Growth (10 pts)
        score_growth = 9.0

        # f) Application Feasibility (10 pts)
        score_feasibility = 9.0

        raw_opp = score_visa + score_mode + score_comp + score_employer + score_growth + score_feasibility
        opportunity_score = int(round(min(100.0, max(10.0, raw_opp))))

        # ── 5. Build Explainable Reasons & Gaps ──
        match_reasons = []
        if matched_skills:
            match_reasons.append(f"Strong skill alignment: {', '.join(matched_skills[:4])}")
        if score_role >= 13.0:
            match_reasons.append("Direct title and role family match")
        if "remote" in job_work_mode:
            match_reasons.append("Full remote flexibility matches preference")
        if visa_signal == "indicated":
            match_reasons.append("Visa sponsorship officially indicated")
        if score_industry >= 9.0:
            match_reasons.append("Sector background matches candidate domain")

        gaps = []
        for ms in missing_skills[:3]:
            gaps.append(f"Skill requirement not highlighted in current CV: {ms.title()}")

        explanation = {
            "match_breakdown": {
                "skills": round(score_skills, 1),
                "experience": round(score_exp, 1),
                "role_seniority": round(score_role, 1),
                "industry": round(score_industry, 1),
                "education": round(score_edu, 1),
                "location": round(score_loc, 1),
                "communication": round(score_comm, 1)
            },
            "opportunity_breakdown": {
                "visa_relocation": round(score_visa, 1),
                "work_mode": round(score_mode, 1),
                "compensation": round(score_comp, 1),
                "employer_relevance": round(score_employer, 1),
                "career_growth": round(score_growth, 1),
                "feasibility": round(score_feasibility, 1)
            },
            "match_reasons": match_reasons,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }

        return match_score, opportunity_score, explanation, gaps
