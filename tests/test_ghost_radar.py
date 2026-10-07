"""Tests for the Ghost Radar engine."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ghost_radar  # noqa: E402


def test_clean_posting_scores_low():
    r = ghost_radar.analyze(
        job_title="Senior Backend Engineer",
        company_name="Acme Fintech Ltd",
        contact_email="talent@acmefintech.com",
        contact_channel="company_portal",
        company_website="acmefintech.com",
        listing_age_days=4,
        salary_listed=True,
        job_description=(
            "Senior Backend Engineer. Reports to the Head of Engineering. You will own "
            "the payments ledger service. Tech stack: Python, Django, PostgreSQL, AWS, "
            "Docker, Kubernetes. Team of 8 engineers. Salary range NGN 8,000,000 - "
            "12,000,000. Interview process: recruiter screen, technical panel, "
            "take-home, final. Benefits: pension, HMO. Requirements: 5+ years Python, "
            "BSc Computer Science. Location: Lagos, hybrid."
        ),
    )
    assert r.risk_score < 25, f"clean posting scored {r.risk_score}"
    assert r.verdict in {"CLEAR", "LOW RISK"}
    assert not r.is_probable_scam
    assert any(s.id == "concrete_jd" for s in r.signals)
    assert any(s.id == "corp_email" for s in r.signals)


def test_payment_demand_is_critical_and_alone_sufficient():
    r = ghost_radar.analyze(
        job_title="Administrative Officer",
        company_name="Federal Ministry",
        contact_text="Congratulations, you have been shortlisted. Pay N50,000 "
                     "registration fee to secure your slot before close of business today.",
        contact_channel="whatsapp",
        payment_requested=True,
        payment_to="individual",
    )
    assert r.verdict == "DANGER"
    assert r.risk_score >= 88
    assert r.is_probable_scam
    assert r.naira_at_risk == 50000
    ids = {s.id for s in r.signals}
    assert "payment_demand" in ids
    assert "pay_individual" in ids
    assert "urgency" in ids
    assert "chat_channel" in ids


def test_naira_extraction_handles_commas():
    r = ghost_radar.analyze(
        contact_text="Send the payment of N350,000 to secure the position.",
        payment_requested=True,
    )
    assert r.naira_at_risk == 350000


def test_task_scam_detected():
    r = ghost_radar.analyze(
        job_title="Remote Product Reviewer",
        contact_text="Subscribe to this YouTube channel and send screenshot as proof. "
                     "Earn per task. Add funds to withdraw. Use your referral code.",
        contact_channel="telegram",
    )
    assert r.is_probable_scam
    assert any(s.id == "task_scheme" for s in r.signals)


def test_spoofed_gov_domain_detected():
    r = ghost_radar.analyze(
        job_title="Graduate Trainee",
        company_name="NNPC Recruitment",
        contact_email="info@nnpc-career.com",
        company_website="nnpc-career.com",
    )
    assert any(s.id == "spoofed_domain" for s in r.signals)
    assert r.is_probable_scam


def test_legit_gov_dot_ng_domain_is_not_flagged_as_spoof():
    r = ghost_radar.analyze(
        company_name="Federal Civil Service Commission",
        contact_email="recruitment@fcsc.gov.ng",
        company_website="fcsc.gov.ng",
        contact_channel="company_portal",
    )
    assert not any(s.id == "spoofed_domain" for s in r.signals)
    assert not r.is_probable_scam


def test_free_email_domain_flagged():
    r = ghost_radar.analyze(
        job_title="Accountant",
        company_name="Bluewave Consulting",
        contact_email="bluewave.hr.recruiter@gmail.com",
    )
    assert any(s.id == "free_email" for s in r.signals)


def test_old_listing_is_ghost_not_scam():
    r = ghost_radar.analyze(
        job_title="Data Analyst",
        company_name="Real Corp",
        contact_email="hr@realcorp.com",
        contact_channel="company_portal",
        listing_age_days=95,
        reposted=True,
        salary_listed=False,
        job_description=("We are looking for a self-starter to join our fast-paced "
                         "environment. Must be a team player, detail oriented, with "
                         "excellent communication skills and a proactive mindset."),
    )
    assert r.is_probable_ghost
    assert not r.is_probable_scam
    assert any(s.id == "age_60" for s in r.signals)
    assert any(s.id == "reposted" for s in r.signals)
    assert any(s.id == "vague_jd" for s in r.signals)
    assert r.hours_at_risk > 0


def test_vague_jd_not_flagged_when_concrete_detail_present():
    r = ghost_radar.analyze(
        job_title="Backend Engineer",
        company_name="Solid Co",
        contact_email="jobs@solid.co",
        listing_age_days=5,
        job_description=("Self-starter wanted for a fast-paced environment, dynamic "
                         "team. Reports to the CTO. Team of 6 engineers. Tech stack: "
                         "Go, PostgreSQL. Salary range $90,000 - $120,000. Interview "
                         "process: 3 rounds. Benefits: pension, health insurance. "
                         "Requirements: 4+ years Go. First project: migrate billing."),
    )
    assert not any(s.id == "vague_jd" for s in r.signals)


def test_verification_steps_present_and_escalate_for_scams():
    clean = ghost_radar.analyze(job_title="Engineer", company_name="Good Co",
                                contact_email="hr@goodco.com")
    scam = ghost_radar.analyze(contact_text="Pay N20,000 processing fee now",
                               payment_requested=True)
    assert len(clean.verification_steps) >= 2
    assert len(scam.verification_steps) > len(clean.verification_steps)
    scam_titles = " ".join(s["title"] for s in scam.verification_steps).lower()
    assert "never pay" in scam_titles
    assert "report" in scam_titles


def test_score_capped_at_100():
    r = ghost_radar.analyze(
        job_title="Easy Remote Work",
        company_name="Quick Cash Ltd",
        contact_text=("URGENT! Pay N25,000 within 10 minutes to activate your portal. "
                      "Guaranteed employment, no experience required, earn N500,000 "
                      "weekly. Your name is on the shortlist already. Connection inside. "
                      "Subscribe to this channel and send screenshot as proof. "
                      "Use referral code. Send the payment to my account number."),
        contact_channel="telegram",
        contact_email="hr.quickcashltd@gmail.com",
        company_website="jiji-jobs-portal.com",
        listing_age_days=120,
        reposted=True,
        salary_listed=False,
        payment_requested=True,
        payment_to="individual",
        interview_mode="text_only",
        unsolicited=True,
        applicant_count=500,
    )
    assert r.risk_score == 100
    assert r.verdict == "DANGER"


def test_agency_name_requires_word_boundary():
    """Regression: 'firs' used to match inside 'first project', flagging a clean
    fintech posting as a government-body impersonation."""
    r = ghost_radar.analyze(
        job_title="Senior Backend Engineer",
        company_name="Acme Fintech Ltd",
        contact_email="talent@acmefintech.com",
        company_website="acmefintech.com",
        contact_channel="company_portal",
        listing_age_days=6,
        salary_listed=True,
        job_description=("Reports to the Head of Engineering. First project: migrate "
                         "the ledger in Q1. Team of 8 engineers. Requirements: 5+ years "
                         "Python. Salary range NGN 9,000,000 - 14,000,000."),
    )
    assert not any(s.id == "agency_claim" for s in r.signals), [s.title for s in r.signals]
    assert r.risk_score == 0, r.risk_score
    assert r.verdict == "CLEAR"


def test_real_agency_mention_still_detected():
    r = ghost_radar.analyze(
        job_title="Graduate Trainee",
        company_name="Recruiters NG",
        contact_email="info@recruitersng.com",
        company_website="recruitersng.com",
        contact_text="We are recruiting for FIRS and the Nigerian Customs Service.",
    )
    assert any(s.id == "agency_claim" for s in r.signals)


@pytest.mark.parametrize("text", ["first project", "firstly", "first of all",
                                  "the first thing"])
def test_first_does_not_trigger_agency(text):
    r = ghost_radar.analyze(job_title="Analyst", job_description=text,
                            company_website="example.com")
    assert not any(s.id == "agency_claim" for s in r.signals)


@pytest.mark.parametrize("raw,domain,label", [
    ("https://fcsc-recruitment.ng/apply", "fcsc-recruitment.ng", "fcsc-recruitment"),
    ("http://example.com:8080/path?x=1", "example.com", "example"),
    ("hr@acmefintech.com", "acmefintech.com", "acmefintech"),
    ("fcsc.gov.ng", "fcsc.gov.ng", "fcsc"),
    ("WWW.NNPC-CAREER.COM", "www.nnpc-career.com", "www.nnpc-career"),
    ("", "", ""),
    ("   ", "", ""),
])
def test_domain_normalisation(raw, domain, label):
    """Regression: split(':')[0] used to reduce 'https://x' to 'https'."""
    assert ghost_radar._normalize_domain(raw) == (domain, label)


def test_real_gov_ng_domain_is_never_a_spoof():
    """Regression: the TLD was stripped before the .gov.ng test, so the test
    could never pass and every federal portal was flagged."""
    for d in ["fcsc.gov.ng", "https://fcsc.gov.ng/vacancies", "recruitment@fcsc.gov.ng",
              "www.recruitment.fedcivilservice.gov.ng", "nnpcgroup.com.ng"]:
        pass
    assert ghost_radar._looks_spoofed("fcsc.gov.ng") is None
    assert ghost_radar._looks_spoofed("https://fcsc.gov.ng/vacancies") is None
    assert ghost_radar._looks_spoofed("recruitment@fcsc.gov.ng") is None
    # ...but a clone still is
    assert ghost_radar._looks_spoofed("fcsc-recruitment.ng") is not None


def test_spoof_detection_needs_label_boundary():
    assert ghost_radar._looks_spoofed("nnpc-career.com")
    assert ghost_radar._looks_spoofed("https://fcsc-recruitment.ng/apply")
    # 'meta' must not match inside an unrelated word
    assert ghost_radar._looks_spoofed("metamorph-jobs.com") is None
    # a plain corporate domain is never a clone
    assert ghost_radar._looks_spoofed("acmefintech.com") is None
    assert ghost_radar._looks_spoofed("paystack.com") is None


def test_all_signals_serialisable():
    r = ghost_radar.analyze(job_title="Test", job_description="Reports to manager. "
                            "Team of 5. Pay N10,000 fee.")
    d = r.as_dict()
    assert d["verdict"] in {"CLEAR", "LOW RISK", "CAUTION", "HIGH RISK", "DANGER"}
    assert isinstance(d["signals"], list)
    assert all("title" in s and "source" in s for s in d["signals"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
