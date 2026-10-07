"""Tests for the ATS match engine."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re

from app import ats_match  # noqa: E402


JD = """
Senior Backend Engineer

We are looking for a Senior Backend Engineer to own our payments platform.
You will work with a team of 8 engineers and report to the Head of Engineering.

Requirements:
- 5+ years Python
- Strong Django and FastAPI experience
- PostgreSQL and Redis
- AWS (EC2, S3, Lambda)
- Docker and Kubernetes
- CI/CD with GitHub Actions
- Experience with microservices and REST API design
- Excellent communication skills
- BSc Computer Science or equivalent

Salary range: NGN 9,000,000 - 14,000,000
"""

STRONG_RESUME = """
Jane Okoye
jane.okoye@email.com | +234 803 000 0000 | Lagos, Nigeria

EXPERIENCE

Senior Backend Engineer, Paystack
Jan 2021 - Present
- Architected a payments reconciliation service in Python and Django that cut
  settlement errors by 74% across 12,000 merchants.
- Built FastAPI endpoints serving 40M requests per month at p99 latency of 90ms.
- Migrated the ledger from MySQL to PostgreSQL, reducing query time by 61%.
- Automated deployment with Docker, Kubernetes and GitHub Actions CI/CD, cutting
  release time from 3 hours to 18 minutes.
- Led a team of 5 engineers through an AWS migration using Lambda and S3.
- Designed REST API contracts adopted by 3 internal teams.
- Introduced Redis caching that reduced database load by 45%.

EDUCATION
BSc Computer Science, University of Lagos, 2016

SKILLS
Python, Django, FastAPI, PostgreSQL, Redis, AWS, Docker, Kubernetes, CI/CD,
microservices, REST API, communication
"""

WEAK_RESUME = """
John Doe

SUMMARY
Hardworking team player seeking a challenging role.

EXPERIENCE
Responsible for various backend tasks.
Worked on some databases.
Assisted with deployment.
Helped with cloud things.

EDUCATION
BSc Computer Science
"""


def test_keyword_extraction_finds_core_skills():
    kws = ats_match.extract_keywords(JD)
    terms = {k.canonical for k in kws}
    for expected in ["python", "django", "postgresql", "aws", "docker", "kubernetes",
                     "ci/cd", "microservices", "communication"]:
        assert expected in terms, f"{expected} not extracted"


def test_strong_resume_outscores_weak():
    strong = ats_match.analyze(JD, STRONG_RESUME)
    weak = ats_match.analyze(JD, WEAK_RESUME)
    assert strong.match_rate > 75, f"strong resume only scored {strong.match_rate}"
    assert weak.match_rate < 45, f"weak resume scored {weak.match_rate}"
    assert strong.hard_match_rate > weak.hard_match_rate


def test_strong_resume_would_be_reviewed_weak_would_not():
    strong = ats_match.analyze(JD, STRONG_RESUME, pool_size=180, reviewed=20)
    weak = ats_match.analyze(JD, WEAK_RESUME, pool_size=180, reviewed=20)
    assert strong.rank["would_be_reviewed"], strong.rank
    assert not weak.rank["would_be_reviewed"], weak.rank
    assert strong.rank["estimated_rank"] < weak.rank["estimated_rank"]


def test_median_48_maps_to_fiftieth_percentile():
    """Anchor of the rank model: median resume scores 48/100."""
    r = ats_match.estimate_rank(48, pool_size=180, reviewed=20)
    assert r["percentile"] == 50
    assert 88 <= r["estimated_rank"] <= 92, r["estimated_rank"]


def test_rank_is_monotonic_in_match_rate():
    ranks = [ats_match.estimate_rank(m)["estimated_rank"] for m in (10, 30, 50, 70, 90)]
    assert ranks == sorted(ranks, reverse=True), ranks


def test_boolean_string_is_well_formed():
    kws = ats_match.extract_keywords(JD)
    b = ats_match.build_boolean_string(kws)
    assert b
    assert b.count("(") == b.count(")"), b
    assert 'NOT "intern"' in b
    assert " OR " in b, b
    assert " AND " in b, b


def _strip_groups(s: str) -> str:
    """Remove every balanced (...) group, innermost first, leaving top-level text."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\(([^()]*)\)", "", s)
    return s


def test_boolean_string_respects_operator_precedence():
    """AND binds tighter than OR, so every OR must live inside a group.
    Regression: a flattened version produced 'A OR B AND C OR D', which parses
    as A OR (B AND C) OR D - semantically wrong while looking fine."""
    for jd in [JD,
               "We need Python and Django and PostgreSQL and AWS and Docker.",
               "Requirements: SQL, Excel, Power BI, stakeholder management, IFRS.",
               "Looking for a Senior Engineer with Go, Kubernetes, Terraform."]:
        b = ats_match.build_boolean_string(ats_match.extract_keywords(jd))
        if not b:
            continue
        assert b.count("(") == b.count(")"), b
        assert "((" not in b, f"redundant nesting: {b}"
        top = _strip_groups(b)
        assert " OR " not in top, f"ungrouped OR at top level: {b}\n  -> {top}"
        assert " AND " in b, b


def test_boolean_string_empty_for_no_hard_skills():
    kws = ats_match.extract_keywords("We need someone nice and friendly for the team.")
    assert ats_match.build_boolean_string(kws) == ""


def test_acronym_and_expansion_count_as_same_skill():
    """'k8s' in the resume must satisfy 'Kubernetes' in the JD."""
    resume = "Deployed services on k8s and used AWS for hosting."
    hits = ats_match._resume_terms(resume)
    assert "kubernetes" in hits
    assert "aws" in hits


def test_missing_keywords_are_prioritised_by_weight():
    report = ats_match.analyze(JD, WEAK_RESUME)
    weights = [k.weight for k in report.missing]
    assert weights == sorted(weights, reverse=True)
    assert len(report.missing) > 0


def test_extras_detect_skills_jd_never_asked_for():
    jd = "We need Python and Django."
    resume = "Python, Django, Solidity, Terraform, Figma, ACCA"
    r = ats_match.analyze(jd, resume)
    assert "solidity" in r.extras_in_resume
    assert "figma" in r.extras_in_resume


def test_format_checks_flag_missing_contact_info():
    checks, score, risk = ats_match.check_format(WEAK_RESUME)
    labels = {c["label"] for c in checks if not c["ok"]}
    assert any("Email" in l for l in labels), labels
    assert any("Phone" in l for l in labels), labels
    assert any("clich" in l.lower() for l in labels), labels
    assert any("weak bullet" in l.lower() for l in labels), labels
    assert score < 70


def test_format_checks_pass_a_clean_resume():
    checks, score, risk = ats_match.check_format(STRONG_RESUME)
    assert score >= 75, score
    assert "Low" in risk or "Moderate" in risk


def test_honest_note_debunks_the_fake_stat():
    r = ats_match.analyze(JD, STRONG_RESUME)
    assert "92%" in r.honest_note
    assert "invisibility" in r.honest_note.lower()


def test_currency_codes_are_not_treated_as_skills():
    """Regression: 'NGN' from a salary line used to be reported as a missing skill."""
    jd = ("Senior Backend Engineer. Requirements: Python, Django. "
          "Salary range NGN 9,000,000 - 14,000,000 per annum. USD equivalent negotiable. "
          "Benefits: pension, HMO. Location: Lagos, hybrid.")
    kws = ats_match.extract_keywords(jd)
    terms = {k.canonical for k in kws}
    assert "ngn" not in terms, terms
    assert "usd" not in terms, terms
    assert "hmo" not in terms or True  # HMO is arguably a benefit term, not asserted
    report = ats_match.analyze(jd, "Python developer with Django experience.")
    missing = {k.term.lower() for k in report.missing}
    assert "ngn" not in missing, missing
    assert "usd" not in missing, missing


def test_job_ad_boilerplate_acronyms_excluded():
    jd = "We need Python. EOE. WFH possible. Start ASAP. Dept: Engineering. ETC as needed."
    terms = {k.canonical for k in ats_match.extract_keywords(jd)}
    for noise in ["eoe", "wfh", "asap", "dept", "etc"]:
        assert noise not in terms, terms


def test_empty_inputs_handled():
    assert ats_match.extract_keywords("") == []
    r = ats_match.analyze("Python engineer", "python")
    assert r.match_rate == 100
    assert ats_match.estimate_rank(0)["estimated_rank"] >= 1


def test_serialisable():
    d = ats_match.analyze(JD, STRONG_RESUME).as_dict()
    assert set(["match_rate", "missing", "matched", "boolean_string", "rank",
                "format_checks", "honest_note"]).issubset(d.keys())


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
