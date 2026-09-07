"""
AI Job Hunter — Profile-Driven Dual Weighted Matching & Scoring Engine
Scores each candidate against each job based on the candidate's own skills,
experience, target roles, and preferences. No hardcoded candidate data.
"""

from typing import Dict, Any, List, Tuple
import re


class MatchingEngine:
    """
    Computes deterministic Match Score & Opportunity Score
    with explainable rationales and verifiable gap reports.
    Fully profile-driven — works for any candidate.
    """

    @staticmethod
    def calculate_scores(
        profile_data: Dict[str, Any],
        job_data: Dict[str, Any],
        job_features: Dict[str, Any]
    ) -> Tuple[int, int, Dict[str, Any], List[str]]:
        """
        Calculate Match Score & Opportunity Score based on candidate profile.
        Returns: (match_score, opportunity_score, explanation_dict, gaps_list)
        """
        # ── 1. Extract Candidate Profile Attributes & Token Variations ──
        candidate_skill_tokens = set()
        for s in profile_data.get("skills", []):
            raw_s = s.get("skill", "").lower().strip()
            if not raw_s:
                continue
            candidate_skill_tokens.add(raw_s)
            for part in re.split(r'[,&/|()]+', raw_s):
                p_clean = part.strip()
                if p_clean:
                    candidate_skill_tokens.add(p_clean)
                for w in p_clean.split():
                    if len(w) > 2 and w not in ["and", "the", "for", "with", "from", "system", "systems"]:
                        candidate_skill_tokens.add(w)

        # Target roles from candidate preferences (no hardcoded fallback)
        candidate_roles = [
            r.lower().strip()
            for r in profile_data.get("preferences_json", {}).get("target_roles", [])
        ]

        candidate_location = (profile_data.get("location") or "worldwide").lower()
        salary_floor = float(profile_data.get("salary_floor") or 0)

        # Candidate experience summary — count experiences for scoring
        experiences = profile_data.get("experiences", [])
        experience_years_estimate = max(len(experiences) * 2, 1)  # rough estimate: ~2 years per role

        # ── 2. Extract Job Attributes ──
        job_title = (job_data.get("title") or "").lower()
        job_desc = (job_data.get("description") or "").lower()
        job_location = (job_data.get("location") or "").lower()
        job_work_mode = (job_data.get("work_mode") or (
            "remote" if any(r in (job_desc + " " + job_location) for r in ["remote", "worldwide", "anywhere"]) else "unknown"
        )).lower()

        # Build domain-relevant skill tokens from the job — use the candidate's own skills as the domain reference
        candidate_domain_skills = list(candidate_skill_tokens)[:30]

        # Extract skills from job description that overlap with candidate's domain
        text_skills = [s for s in candidate_domain_skills if s in job_desc or s in job_title]
        raw_feat_skills = [s.lower().strip() for s in job_features.get("skills_json", []) if s]

        # Combine and deduplicate
        all_job_skills = list(dict.fromkeys(raw_feat_skills + text_skills))
        if not all_job_skills:
            all_job_skills = text_skills or ["domain experience"]

        visa_signal = job_features.get("visa_signal", "unknown")
        if any(term in (job_desc + " " + job_data.get("raw_html", "")) for term in ["visa sponsor", "sponsorship", "visa supported", "relocation supported"]):
            visa_signal = "sponsored"
        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        currency = job_data.get("currency", "NGN")

        # ── 3. Compute Match Score (0 - 100) ──

        # DISQUALIFIER CHECK: If candidate has target roles, check if this job is in a completely unrelated domain
        # Build disqualification from the absence of any role overlap
        has_any_role_signal = False
        if candidate_roles:
            for target in candidate_roles:
                target_words = [w for w in target.split() if len(w) > 2]
                if target in job_title or any(w in job_title for w in target_words if len(w) > 3):
                    has_any_role_signal = True
                    break

        # a) Skills Fit (30 pts)
        matched_skills = [
            s for s in all_job_skills
            if any(tok in s or s in tok for tok in candidate_skill_tokens)
        ]
        missing_skills = [s for s in all_job_skills if s not in matched_skills]
        skill_ratio = len(matched_skills) / max(len(all_job_skills), 1) if all_job_skills else 0.5
        score_skills = min(30.0, max(5.0 if matched_skills else 0.0, skill_ratio * 30.0))

        # b) Experience Fit (20 pts) — based on actual experience count from profile
        if experience_years_estimate >= 8:
            score_exp = 19.0
        elif experience_years_estimate >= 5:
            score_exp = 16.0
        elif experience_years_estimate >= 3:
            score_exp = 13.0
        elif experience_years_estimate >= 1:
            score_exp = 10.0
        else:
            score_exp = 5.0

        # c) Role / Seniority Fit (15 pts)
        # Determine role relevance based on candidate's target_roles matching job title
        score_role = 0.0
        if candidate_roles:
            for target in candidate_roles:
                target_words = [w for w in target.split() if len(w) > 2]
                if target in job_title or (target_words and all(w in job_title for w in target_words)):
                    score_role = 15.0
                    break
                elif any(w in job_title for w in target_words if len(w) > 3):
                    score_role = max(score_role, 12.0)

            # If no role matched at all and candidate has target roles, give minimal score
            if score_role == 0.0:
                # Check if there's at least some keyword overlap with any candidate skill
                if matched_skills:
                    score_role = 5.0
                else:
                    score_role = 0.0
        else:
            # No target roles specified — give neutral score based on skill match
            score_role = 8.0 if matched_skills else 3.0

        # If no role relevance AND no skill match, this job is likely irrelevant
        if score_role == 0.0 and score_skills <= 5.0:
            return 0, 0, {
                "match_reasons": [],
                "summary": "No relevant role or skill overlap found for this candidate",
                "matched_skills": []
            }, ["Role and skills do not match candidate's profile"]

        # d) Industry / Domain Fit (10 pts) — neutral for all candidates, boost on keyword overlap
        candidate_sectors = set()
        for exp in experiences:
            if exp.get("sector"):
                candidate_sectors.add(exp["sector"].lower())

        score_industry = 7.0
        if candidate_sectors:
            if any(s in job_desc for s in candidate_sectors):
                score_industry = 10.0
            elif any(term in job_desc for term in ["ngo", "humanitarian", "health", "fintech", "enterprise", "telecom", "ai", "cloud"]):
                score_industry = 9.0
        else:
            score_industry = 8.0  # Neutral if no sector data

        # e) Education / Certifications Fit (10 pts)
        certs_count = len(profile_data.get("certifications", []))
        edu_count = len(profile_data.get("education", []))
        if certs_count >= 3 and edu_count >= 1:
            score_edu = 10.0
        elif certs_count >= 1 or edu_count >= 1:
            score_edu = 8.0
        else:
            score_edu = 5.0

        # f) Location Fit (10 pts) — based on candidate's preferred work modes
        preferred_modes = profile_data.get("preferences_json", {}).get("work_modes", ["remote", "hybrid", "onsite"])
        score_loc = 5.0
        if "remote" in preferred_modes and ("remote" in job_work_mode or "remote" in job_location or "worldwide" in job_location):
            score_loc = 10.0
        elif "hybrid" in preferred_modes and "hybrid" in job_work_mode:
            score_loc = 8.0
        elif "onsite" in preferred_modes:
            # Check if candidate location matches job location
            if candidate_location and candidate_location in job_location:
                score_loc = 9.0
            else:
                score_loc = 6.0
        elif "remote" in job_work_mode or "worldwide" in job_location:
            score_loc = 9.0  # Remote is generally good for everyone

        # g) Communication / Transferable Skills (5 pts) — neutral for all candidates
        score_comm = 4.0

        raw_match = score_skills + score_exp + score_role + score_industry + score_edu + score_loc + score_comm
        match_score = int(round(min(100.0, max(10.0, raw_match))))

        # ── 4. Compute Opportunity Score (0 - 100) ──
        # Formula: 25% visa + 20% work-mode + 20% comp + 15% employer + 10% growth + 10% feasibility

        # a) Visa / Relocation (25 pts)
        if visa_signal in ["indicated", "sponsored"]:
            score_visa = 25.0
        elif visa_signal == "possible":
            score_visa = 18.0
        elif visa_signal in ["unknown", None]:
            score_visa = 14.0
        else:
            score_visa = 6.0

        # b) Work Mode / Location Preference (20 pts) — driven by candidate preferences
        if "remote" in job_work_mode and "remote" in preferred_modes:
            score_mode = 20.0
        elif "hybrid" in job_work_mode and "hybrid" in preferred_modes:
            score_mode = 16.0
        elif "remote" in job_work_mode:
            score_mode = 14.0  # Remote is good even if not explicitly preferred
        else:
            score_mode = 10.0

        # c) Compensation Quality (20 pts) — against candidate's salary_floor
        score_comp = 14.0  # Default neutral if unknown
        if salary_max or salary_min:
            effective_sal = salary_max or salary_min
            if currency in ["USD", "EUR", "GBP"]:
                score_comp = 20.0
            elif salary_floor > 0 and effective_sal >= salary_floor:
                score_comp = 18.0
            elif salary_floor > 0 and effective_sal < salary_floor:
                score_comp = 8.0
            else:
                score_comp = 16.0

        # d) Employer / Sector Relevance (15 pts)
        score_employer = 12.0
        if any(term in job_desc for term in ["united nations", "ngo", "international", "global", "red cross", "who"]):
            score_employer = 15.0

        # e) Seniority / Career Growth (10 pts)
        score_growth = 9.0

        # f) Application Feasibility (10 pts)
        has_direct_email = ("@" in job_desc) or ("@" in str(job_data.get("raw_html", ""))) or bool(job_data.get("recruiter_email"))
        score_feasibility = 10.0 if has_direct_email else 8.0

        raw_opp = score_visa + score_mode + score_comp + score_employer + score_growth + score_feasibility
        opportunity_score = int(round(min(100.0, max(10.0, raw_opp))))

        # ── 5. Build Explainable Reasons & Gaps ──
        match_reasons = []
        if matched_skills:
            match_reasons.append(f"Strong skill alignment: {', '.join(matched_skills[:4])}")
        if score_role >= 12.0:
            match_reasons.append("Direct title and role family match")
        if has_direct_email:
            match_reasons.append("Verified HR email detected — ready for direct dispatch")
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
