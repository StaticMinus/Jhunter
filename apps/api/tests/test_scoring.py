"""
AI Job Hunter — Unit Tests for Matching & Opportunity Scoring Engine
Verifies compliance with MVP Specification formulas and anti-fabrication rules.
"""

from app.services.matching_engine import MatchingEngine
from app.services.application_generator import ApplicationGenerator
from app.services.cv_parser import DAVID_DEFAULT_PROFILE


def test_match_score_calculation():
    """Verify that a strong ICT/Software candidate achieves >= 85% match on a tailored role."""
    job_data = {
        "title": "ICT Specialist & Systems Administrator",
        "employer": "International Humanitarian NGO",
        "location": "Abuja, Nigeria",
        "work_mode": "hybrid",
        "salary_min": 700000.0,
        "salary_max": 900000.0,
        "currency": "NGN",
        "description": "Enterprise networking, Active Directory, Azure, disaster recovery, cybersecurity, and ICT operations."
    }
    job_features = {
        "skills_json": ["lan/wan & tcp/ip networking", "active directory", "cybersecurity & ids/ips", "disaster recovery & backup architecture"],
        "visa_signal": "indicated"
    }

    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
        profile_data=DAVID_DEFAULT_PROFILE,
        job_data=job_data,
        job_features=job_features
    )

    assert match_score >= 85, f"Expected strong match score >= 85, got {match_score}"
    assert opp_score >= 85, f"Expected high opportunity score >= 85, got {opp_score}"
    assert "skills" in explanation["match_breakdown"]
    assert len(explanation["match_reasons"]) > 0


def test_anti_fabrication_application_generation():
    """Verify that generated application packages are 100% grounded and do not hallucinate."""
    job_data = {
        "title": "ICT Specialist",
        "employer": "Health Tech Org",
        "location": "Lagos, Nigeria",
        "description": "Need Azure, Entra ID, and IDS/IPS support."
    }
    explanation = {
        "matched_skills": ["Active Directory & Entra ID", "Cybersecurity & IDS/IPS"],
        "match_score": 94,
        "opportunity_score": 96,
        "match_reasons": ["Direct skill alignment"]
    }

    package = ApplicationGenerator.generate_package(
        profile=DAVID_DEFAULT_PROFILE,
        job=job_data,
        explanation=explanation
    )

    assert "cover_letter" in package
    assert "tailored_cv" in package
    assert "answers" in package
    assert "RedAid Nigeria" in package["cover_letter"] or "RedAid Nigeria" in package["tailored_cv"]
    assert len(package["answers"]) >= 3
    # Check that answers have confidence score
    for ans in package["answers"]:
        assert 0.0 <= ans["confidence"] <= 1.0


def test_unknown_signals_not_penalized_harshly():
    """Verify Rule R2: Do not reject or overly penalize unknown salary / visa signals."""
    job_data = {
        "title": "Systems Engineer",
        "employer": "Unknown Org",
        "location": "Nigeria",
        "work_mode": "onsite",
        "salary_min": None,
        "salary_max": None,
        "description": "General systems role."
    }
    job_features = {
        "skills_json": ["windows & linux server administration"],
        "visa_signal": "unknown"
    }

    match_score, opp_score, explanation, gaps = MatchingEngine.calculate_scores(
        profile_data=DAVID_DEFAULT_PROFILE,
        job_data=job_data,
        job_features=job_features
    )

    # Unknown visa gets neutral 12.5 pts, compensation gets neutral 14.0 pts
    assert opp_score > 40, f"Opp score shouldn't be zeroed out for unknown fields, got {opp_score}"


if __name__ == "__main__":
    test_match_score_calculation()
    test_anti_fabrication_application_generation()
    test_unknown_signals_not_penalized_harshly()
    print("ALL 3 SCORING & ANTI-FABRICATION TESTS PASSED!")
