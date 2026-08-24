"""
AI Job Hunter — Unit Tests for Deduplication Engine
"""

from workers.deduplication import Deduplicator


def test_url_normalization():
    url_raw = "https://reliefweb.int/job/12345?utm_source=twitter&utm_medium=social&ref=feed#anchor"
    cleaned = Deduplicator.clean_canonical_url(url_raw)
    assert "utm_source" not in cleaned
    assert "utm_medium" not in cleaned
    assert "ref" not in cleaned
    assert cleaned.startswith("https://reliefweb.int/job/12345")


def test_duplicate_detection():
    existing = [
        {
            "canonical_url": "https://reliefweb.int/job/100",
            "title": "ICT Specialist",
            "employer": "RedAid",
            "description": "Enterprise networking and cybersecurity support.",
            "raw_hash": Deduplicator.compute_fingerprint("ICT Specialist", "RedAid", "Enterprise networking and cybersecurity support.")
        }
    ]

    # Duplicate by URL with tracking params
    new_job_1 = {
        "canonical_url": "https://reliefweb.int/job/100?utm_campaign=daily",
        "title": "ICT Specialist",
        "employer": "RedAid",
        "description": "Different wording but exact same canonical URL."
    }
    is_dup, reason = Deduplicator.is_duplicate(new_job_1, existing)
    assert is_dup is True

    # Duplicate by title & employer
    new_job_2 = {
        "canonical_url": "https://different-source.com/job/200",
        "title": "ICT Specialist",
        "employer": "RedAid",
        "description": "Enterprise networking."
    }
    is_dup2, reason2 = Deduplicator.is_duplicate(new_job_2, existing)
    assert is_dup2 is True

    # Unique new job
    unique_job = {
        "canonical_url": "https://reliefweb.int/job/999",
        "title": "Senior Python Architect",
        "employer": "Global Tech Hub",
        "description": "Brand new position."
    }
    is_dup3, _ = Deduplicator.is_duplicate(unique_job, existing)
    assert is_dup3 is False


if __name__ == "__main__":
    test_url_normalization()
    test_duplicate_detection()
    print("PASSED: All Deduplication tests passed cleanly!")
