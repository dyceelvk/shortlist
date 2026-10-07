"""
Ghost Radar - job authenticity & scam-risk engine.

Every rule in this file is traceable to published research on ghost jobs and
recruitment fraud. See RESEARCH.md for the source of each signal.

Design principles
-----------------
1. Money-for-job is an absolute line, not a weighted factor. No legitimate
   employer on earth charges a candidate to be hired. Any payment demand is a
   CRITICAL signal that caps the verdict in the DANGER band on its own.
2. Ghost jobs (real company, no real req) and outright scams (fake company,
   real theft) are scored on the same scale but reported separately, because
   the remedy differs: a ghost costs you time, a scam costs you money.
3. Every fired signal carries a human-readable reason and a source, so the
   user can see *why* the tool thinks what it thinks. No black-box scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["critical", "high", "medium", "low", "positive"]

# --------------------------------------------------------------------------
# Lexicons. These are the actual phrases scammers use, harvested from victim
# reports and recruiter-fraud advisories (FlexJobs 2026, Recruitment Boss NG
# 2026, Punch NG, NewsClick NG).
# --------------------------------------------------------------------------

MONEY_DEMAND = [
    r"registration fee", r"processing fee", r"application fee", r"application form",
    r"medical fee", r"medicals?", r"uniform", r"induction fee", r"training fee",
    r"training programme", r"business course", r"visa processing", r"processing charge",
    r"secure your slot", r"secure a slot", r"activation fee", r"profile upgrade",
    r"verification fee", r"documentation fee", r"background check fee", r"screening fee",
    r"id card fee", r"laptop fee", r"confirmation fee", r"slot fee", r"placement fee",
    r"refundable deposit", r"pay(?:ment)? to (?:confirm|secure|process|activate)",
    r"send (?:the )?(?:money|payment|cash|transfer)", r"make a payment", r"pay before",
    r"gift card", r"giftcard", r"buy (?:airtime|data|crypto)", r"bitcoin", r"usdt",
    r"account number", r"account details for payment", r"pay into", r"remita(?:-linked)? payment to an individual",
    r"bank details", r"wire (?:transfer|fee)",
]

URGENCY = [
    r"within \d+ (?:minutes?|hours?)", r"today only", r"limited slots?", r"only \d+ (?:slots?|spots?)",
    r"act (?:fast|now|quickly)", r"hurry", r"urgent(?:ly)?(?:!+)?", r"immediately",
    r"expires? (?:today|tonight|soon)", r"don'?t miss", r"do not miss", r"last chance",
    r"first come", r"slots? (?:are )?filling", r"deadline is today", r"respond within",
    r"before (?:close of business|cob) today", r"offer (?:will be )?withdrawn",
]

TOO_GOOD = [
    r"no experience (?:needed|required|necessary)", r"no qualification",
    r"no interview", r"guaranteed (?:employment|placement|job|hiring|income)",
    r"100% placement", r"assured (?:employment|placement)", r"automatic (?:employment|selection)",
    r"earn (?:up to )?(?:₦|naira|n)?\s?\d{3,}", r"make (?:up to )?(?:₦|naira)?\s?\d{3,}",
    r"double your (?:money|investment|income)", r"get paid to (?:like|watch|review)",
    r"passive income", r"work from anywhere", r"be your own boss",
    r"rags to riches", r"financial freedom",
]

INSIDER_CLAIMS = [
    r"connection inside", r"insider", r"i know someone (?:in|at|inside)",
    r"push your name", r"your name (?:is )?(?:on|in) the (?:short ?list|list)",
    r"already shortlisted", r"you have been selected", r"recommended list",
    r"slot (?:has been )?reserved (?:for you)?",
]

TASK_SCAM = [
    r"review products?", r"like (?:videos?|posts?)", r"subscribe to (?:this )?(?:youtube|channel)",
    r"screenshot (?:as )?proof", r"referral code", r"upgrade to withdraw",
    r"complete (?:the )?tasks?", r"commission per task", r"earn per task",
    r"add (?:funds|money) to withdraw", r"unlock (?:the )?portal", r"task portal",
    r"order (?:and )?(?:rate|review)",
]

NIGERIAN_AGENCIES = [
    "nnpc", "cbn", "npa", "nimc", "customs", "immigration", "fcsc",
    "fedcivilservice", "ohcsf", "nigerian army", "air force", "navy",
    "police force", "nigerian police", "firs", "nse", "sec nigeria",
    "frsc", "ndic", "nigerian ports", "federal civil service",
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "proton.me", "protonmail.com", "icloud.com", "ymail.com", "mail.com",
    "zoho.com", "gmx.com",
}

CHAT_FIRST_CHANNELS = {"whatsapp", "telegram", "sms", "text", "instagram", "facebook", "twitter", "x", "signal"}

BUZZWORDS = [
    "self-starter", "self starter", "fast-paced environment", "fast paced environment",
    "dynamic team", "think outside the box", "wear many hats", "wear multiple hats",
    "go-getter", "go getter", "rockstar", "ninja", "guru", "wizard",
    "passionate individual", "hard worker", "team player", "detail oriented",
    "detail-oriented", "excellent communication skills", "ability to multitask",
    "results driven", "results-driven", "proactive mindset", "can-do attitude",
]

# Markers of a JD written by a real hiring manager with a real problem to solve.
CONCRETE_MARKERS = [
    r"report(?:s|ing)? to", r"you will (?:work|own|lead|build|ship|manage)",
    r"first (?:90 days|project|quarter)", r"tech stack", r"our stack",
    r"team of \d", r"\d+ (?:engineers?|designers?|analysts?|people|reports)",
    r"salary range", r"compensation range", r"\b(?:₦|\$|€|£)\s?\d[\d,]*(?:\s?[-–]\s?(?:₦|\$|€|£)?\s?\d[\d,]*)?",
    r"interview process", r"our (?:interview|process) (?:consists|involves|has)",
    r"start(?:ing)? (?:date|in) ", r"benefits", r"pension", r"hmo", r"health insurance",
    r"performance review", r"kpi", r"okr", r"deliverables?", r"quarterly goals?",
    r"stack:?", r"requirements?:", r"responsibilities?:", r"location:", r"hybrid",
    r"\d+ years", r"\d+\+ years", r"bachelor", r"b\.?sc", r"hnd", r"on site", r"onsite",
]

# Known brand stems scammers clone (Recruitment Boss NG 2026, Punch NG 2026).
BRAND_STEMS = [
    "nnpc", "fcsc", "npa", "cbn", "nimc", "payporte", "jiji", "dangote", "mtn",
    "gtbank", "gtb", "accessbank", "zenithbank", "firstbank", "unilever", "nestle",
    "shell", "chevron", "totalenergies", "pwc", "kpmg", "deloitte", "ernst",
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "openai",
    "unilever", "flourmills", "guinness", "nigerianbreweries", "andela",
]
SPOOF_SUFFIXES = [
    "recruitment", "recruit", "career", "careers", "jobs", "job", "vacancy",
    "vacancies", "hiring", "apply", "application", "portal", "employment", "hr",
]

Verdict = Literal["CLEAR", "LOW RISK", "CAUTION", "HIGH RISK", "DANGER"]


@dataclass
class Signal:
    id: str
    severity: Severity
    title: str
    detail: str
    source: str
    weight: int = 0
    evidence: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "source": self.source,
            "weight": self.weight,
            "evidence": self.evidence,
        }


@dataclass
class GhostReport:
    risk_score: int
    verdict: Verdict
    is_probable_scam: bool
    is_probable_ghost: bool
    signals: list[Signal] = field(default_factory=list)
    naira_at_risk: int = 0
    hours_at_risk: float = 0.0
    verification_steps: list[dict] = field(default_factory=list)
    summary: str = ""

    def as_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "verdict": self.verdict,
            "is_probable_scam": self.is_probable_scam,
            "is_probable_ghost": self.is_probable_ghost,
            "signals": [s.as_dict() for s in self.signals],
            "naira_at_risk": self.naira_at_risk,
            "hours_at_risk": self.hours_at_risk,
            "verification_steps": self.verification_steps,
            "summary": self.summary,
        }


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def _haystack(*parts: str) -> str:
    return "\n".join(p or "" for p in parts).lower()


def _find(patterns: list[str], text: str) -> list[str]:
    hits = []
    for p in patterns:
        m = re.search(p, text)
        if m:
            hits.append(m.group(0).strip())
    return hits


def _extract_naira(*parts: str) -> int:
    """Pull the largest money figure mentioned, in naira."""
    text = " ".join(p or "" for p in parts)
    amounts: list[int] = []
    for m in re.finditer(r"(?:₦|naira|n)\s?(\d{1,3}(?:[,.\s]\d{3})+|\d{3,})", text, re.I):
        raw = re.sub(r"[,.\s]", "", m.group(1))
        try:
            amounts.append(int(raw))
        except ValueError:
            continue
    return max(amounts) if amounts else 0


def _email_domain(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].strip().rstrip(".")


_AGENCY_RE = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(a) for a in NIGERIAN_AGENCIES) + r")(?![a-z])")
_TLD_RE = re.compile(r"\.(com|org|net|io|edu|gov|co|ng|uk|us|za|ke|gh|ca|de|fr|in)(\.\w+)?$")


def _normalize_domain(raw: str) -> tuple[str, str]:
    """
    Reduce any of 'https://x.ng/apply', 'x.ng:8080', 'hr@x.ng' or 'x.ng' to
    (full_domain, label_without_tld). Returns ('', '') for empty input.

    Order matters: the scheme must be stripped before the port, or splitting on
    ':' eats 'https:' and leaves nothing but the scheme.
    """
    s = (raw or "").strip().lower()
    if not s:
        return "", ""
    if "@" in s:
        s = s.rsplit("@", 1)[1]
    s = re.sub(r"^[a-z][a-z0-9+.-]*://", "", s)
    s = s.split("/")[0].split("?")[0].split("#")[0]
    if re.search(r":\d+$", s):
        s = s.rsplit(":", 1)[0]
    s = s.strip(".")
    label = _TLD_RE.sub("", s)
    return s, label


def _looks_spoofed(raw: str) -> str | None:
    """Detect brand-clone domains like nnpc-career.com or fcsc-recruitment.ng."""
    domain, label = _normalize_domain(raw)
    if not domain or not label:
        return None

    for stem in BRAND_STEMS:
        # The stem must be a whole token: 'meta' must not match inside
        # 'metamorph', nor 'apple' inside 'pineapple'. A leading boundary alone
        # is not enough, because 'meta' starts 'metamorph'.
        if not re.search(r"(?<![a-z])" + re.escape(stem) + r"(?![a-z])", label):
            continue
        for suf in SPOOF_SUFFIXES:
            if re.search(re.escape(suf) + r"([^a-z]|$)", label):
                return (f"'{domain}' combines a known brand stem ('{stem}') with a "
                        f"recruitment suffix ('{suf}'). Official recruiters almost "
                        f"never use this pattern.")

    # Government impersonation: names a federal body but is not on .gov.ng.
    # Tested against the FULL domain (the label has had .gov.ng stripped from it)
    # and with word boundaries, so 'firs' cannot match inside 'first'.
    m = _AGENCY_RE.search(label)
    if m and not domain.endswith("gov.ng"):
        return (f"'{domain}' names a Nigerian government body ({m.group(1).upper()}) "
                f"but is not on .gov.ng. Real federal recruitment runs through "
                f".gov.ng portals.")
    return None


# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------

def analyze(
    *,
    job_title: str = "",
    company_name: str = "",
    job_description: str = "",
    contact_text: str = "",
    contact_email: str = "",
    contact_channel: str = "",
    company_website: str = "",
    listing_age_days: int | None = None,
    reposted: bool = False,
    salary_listed: bool | None = None,
    payment_requested: bool | None = None,
    payment_to: str = "none",
    interview_mode: str = "",
    unsolicited: bool = False,
    applicant_count: int | None = None,
) -> GhostReport:
    """Score a job posting / recruiter contact for ghost-job and scam risk."""

    signals: list[Signal] = []
    text = _haystack(job_title, job_description, contact_text, company_name)

    # ---- 1. Payment demand: the absolute line ---------------------------
    money_hits = _find(MONEY_DEMAND, text)
    explicit_payment = payment_requested is True
    if explicit_payment or money_hits:
        ev = ", ".join(f'"{h}"' for h in money_hits[:6]) if money_hits else "payment requested"
        signals.append(Signal(
            id="payment_demand",
            severity="critical",
            title="You are being asked to pay to get this job",
            detail="No legitimate employer charges a candidate for registration, forms, "
                   "processing, medicals, uniforms, training, visas, or 'securing a slot'. "
                   "This is the single most reliable fraud signal in existence and the #1 "
                   "recruitment scam in Nigeria. Genuine induction costs are always borne "
                   "by the employer.",
            source="Recruitment Boss NG (2026), FlexJobs '30 Job Scams' (2026), "
                   "NewsClick NG victim reports (2026)",
            weight=60,
            evidence=ev,
        ))

    if payment_to == "individual":
        signals.append(Signal(
            id="pay_individual",
            severity="critical",
            title="Payment goes to a personal account",
            detail="Legitimate Nigerian institutions collect via Remita or a corporate "
                   "account tied to the institution's registered name. A personal account "
                   "name is untraceable and unrecoverable.",
            source="Recruitment Boss NG (2026)",
            weight=25,
        ))

    naira = _extract_naira(job_description, contact_text)
    if naira and (explicit_payment or money_hits):
        signals.append(Signal(
            id="amount_stated",
            severity="high",
            title=f"A specific sum of ₦{naira:,} is being demanded",
            detail=f"Victims in documented Nigerian cases lost between ₦20,000 and "
                   f"₦500,000 to exactly this pattern. The amount is calibrated to be "
                   f"painful but 'borrowable'.",
            source="NewsClick NG (2026): victims lost ₦20k–₦350k; Kano police arrested "
                   "a man over a ₦40m job scam (Peoples Gazette, 2026)",
            weight=10,
            evidence=f"₦{naira:,}",
        ))

    # ---- 2. Insider / already-shortlisted claims ------------------------
    insider = _find(INSIDER_CLAIMS, text)
    if insider:
        signals.append(Signal(
            id="insider_claim",
            severity="critical",
            title="Claims you are 'already shortlisted' or has an 'insider connection'",
            detail="Real shortlists are published only on official portals or sent as "
                   "formal letters on letterhead. Nobody sells access to one. Messages "
                   "of this type are usually paired with fake PDFs mixing real names "
                   "with yours.",
            source="Recruitment Boss NG (2026), scam types 3 and 5",
            weight=35,
            evidence=", ".join(f'"{h}"' for h in insider[:3]),
        ))

    # ---- 3. Task / MLM scheme ------------------------------------------
    tasks = _find(TASK_SCAM, text)
    if tasks:
        signals.append(Signal(
            id="task_scheme",
            severity="critical",
            title="This is a task or investment scheme, not a job",
            detail="The 'review products / like videos / upgrade to withdraw' pattern is "
                   "a Ponzi task scam. Early small payouts are deliberate, designed to "
                   "lower your suspicion before the big deposit is requested.",
            source="Punch NG, 'How Nigerians fall victim to transnational remote job "
                   "scams' (2026)",
            weight=50,
            evidence=", ".join(f'"{h}"' for h in tasks[:4]),
        ))

    # ---- 4. Urgency pressure -------------------------------------------
    urg = _find(URGENCY, text)
    if urg:
        signals.append(Signal(
            id="urgency",
            severity="high" if len(urg) > 1 else "medium",
            title="Manufactured urgency",
            detail="Real hiring moves at the speed of a budget approval. Scammers "
                   "compress your decision window so you cannot verify anything. "
                   "'Pay within 10 minutes' is never a real employer.",
            source="FlexJobs '30 Job Scams' (2026), red-flag list",
            weight=18 if len(urg) > 1 else 10,
            evidence=", ".join(f'"{h}"' for h in urg[:5]),
        ))

    # ---- 5. Too-good-to-be-true ----------------------------------------
    ttg = _find(TOO_GOOD, text)
    if ttg:
        signals.append(Signal(
            id="too_good",
            severity="high",
            title="The offer is better than the market can support",
            detail="High pay plus zero requirements plus no interview is not an "
                   "opportunity, it is bait. Scammers exploit desperation by pricing "
                   "the fantasy above anything a real employer would post.",
            source="FlexJobs (2026), Indeed scam-title analysis",
            weight=20,
            evidence=", ".join(f'"{h}"' for h in ttg[:4]),
        ))

    # ---- 6. Channel and identity ---------------------------------------
    ch = (contact_channel or "").strip().lower()
    if ch in CHAT_FIRST_CHANNELS:
        signals.append(Signal(
            id="chat_channel",
            severity="high",
            title=f"Recruiting happens over {ch.title()}",
            detail="Corporations recruit through their ATS, careers page, or corporate "
                   "email domain. A personal WhatsApp or Telegram number is the delivery "
                   "mechanism for nearly every documented Nigerian job scam.",
            source="NewsClick NG (2026), Punch NG (2026), FlexJobs (2026)",
            weight=22,
        ))

    if unsolicited and ch in CHAT_FIRST_CHANNELS:
        signals.append(Signal(
            id="unsolicited_chat",
            severity="high",
            title="They contacted you first, out of the blue",
            detail="You never applied, yet they have your number and a role for you. "
                   "This is cold outreach with a hook, not sourcing.",
            source="FlexJobs (2026): unsolicited offers are a primary red flag",
            weight=14,
        ))

    dom = _email_domain(contact_email)
    if dom and dom in FREE_EMAIL_DOMAINS:
        signals.append(Signal(
            id="free_email",
            severity="medium",
            title=f"Recruiter email is on a free domain ({dom})",
            detail="A company that cannot issue you an email address on its own domain "
                   "usually does not exist, or is not the one contacting you.",
            source="FlexJobs (2026): generic email domains",
            weight=12,
            evidence=contact_email,
        ))

    spoof = _looks_spoofed(dom) or _looks_spoofed(company_website)
    if spoof:
        signals.append(Signal(
            id="spoofed_domain",
            severity="critical",
            title="The web address is a brand clone",
            detail=spoof + " Go to the organisation's site yourself by typing the "
                   "address you already know, never by following a link.",
            source="Recruitment Boss NG (2026): fcsc-recruitment.ng, nnpc-career.com; "
                   "Punch NG (2026): Payportepro vs PayPorté",
            weight=45,
        ))

    # Word-boundary match only. A naive substring test matches "firs" inside
    # "first project" and fires on ordinary postings.
    agency_hit = next(
        (a for a in NIGERIAN_AGENCIES
         if re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", text)),
        None,
    )
    if agency_hit and not (company_website or "").strip().lower().endswith("gov.ng"):
        signals.append(Signal(
            id="agency_claim",
            severity="medium",
            title=f"Claims to recruit for a government body ({agency_hit.upper()})",
            detail="Federal recruitment is centralised and free. If this contact is not "
                   "on a .gov.ng domain, it is impersonating the agency.",
            source="Recruitment Boss NG (2026)",
            weight=14,
            evidence=agency_hit.upper(),
        ))

    if interview_mode in {"text_only", "chat", "none"}:
        signals.append(Signal(
            id="no_live_interview",
            severity="high",
            title="No live interview of any kind",
            detail="Hiring without a real-time conversation on a secure video call or in "
                   "person is not hiring. Text-only 'interviews' exist to keep the "
                   "victim from hearing a voice or seeing a face.",
            source="FlexJobs (2026): no live interaction, rushed interviews",
            weight=20,
        ))

    # ---- 7. Ghost-job signals (real company, no real req) ---------------
    if listing_age_days is not None and listing_age_days >= 60:
        signals.append(Signal(
            id="age_60",
            severity="high",
            title=f"Listing is {listing_age_days} days old",
            detail="A funded role typically fills in 30–60 days. Anything older than that "
                   "with no description change is either a resume-harvesting pipeline or "
                   "a requisition that lost its budget.",
            source="VidCruiter (2026), job200 Huntr Q1-2026 study of 240,000 applications, "
                   "HideJobs (2026)",
            weight=22,
            evidence=f"{listing_age_days} days",
        ))
    elif listing_age_days is not None and listing_age_days >= 30:
        signals.append(Signal(
            id="age_30",
            severity="medium",
            title=f"Listing is {listing_age_days} days old",
            detail="Past the 30-day mark. High-quality roles are flooded within 72 hours "
                   "and usually move. Verify the role is still live on the company's own "
                   "careers page before spending time tailoring.",
            source="job200 (2026), jobsolv (2026)",
            weight=12,
            evidence=f"{listing_age_days} days",
        ))

    if reposted:
        signals.append(Signal(
            id="reposted",
            severity="medium",
            title="This role keeps being reposted",
            detail="A role that resets its date every few weeks has never been filled and "
                   "may never be. Evergreen postings are honest about being pipelines, "
                   "which means no req, no timeline, no urgency.",
            source="HideJobs (2026), jobsolv (2026), VidCruiter (2026)",
            weight=14,
        ))

    if salary_listed is False:
        signals.append(Signal(
            id="no_salary",
            severity="low",
            title="No compensation stated",
            detail="Real urgent hires include pay to attract serious candidates quickly. "
                   "Omitting it correlates with speculative or pipeline postings. On its "
                   "own this is weak evidence; stacked with other flags it matters.",
            source="jobsolv (2026), Resume Genius 2026 report (41% flag undisclosed pay)",
            weight=5,
        ))

    buzz = [b for b in BUZZWORDS if b in text]
    concrete = [m for m in _find(CONCRETE_MARKERS, text)]
    if len(buzz) >= 3 and len(concrete) <= 2:
        signals.append(Signal(
            id="vague_jd",
            severity="medium",
            title="Description is buzzwords with no concrete substance",
            detail=f"Heavy on filler ({', '.join(buzz[:4])}) with almost no specifics: no "
                   f"reporting line, no team size, no deliverables, no first project. "
                   f"Real JDs are written by a hiring manager who needs a specific "
                   f"problem solved; ghost posts read like templates because they are.",
            source="VidCruiter (2026), HideJobs (2026), jobsolv (2026)",
            weight=16,
            evidence=", ".join(buzz[:5]),
        ))

    if applicant_count is not None and applicant_count >= 100 and (listing_age_days or 0) >= 21:
        signals.append(Signal(
            id="flooded_old",
            severity="medium",
            title=f"{applicant_count}+ applicants on an old listing",
            detail="LinkedIn caps the display at 'over 100 applicants'. An old listing "
                   "still sitting at that threshold has likely been untouched for weeks.",
            source="HideJobs (2026)",
            weight=8,
            evidence=f"{applicant_count}+ applicants",
        ))

    # ---- 8. Positive (risk-reducing) evidence ---------------------------
    positives: list[Signal] = []
    if len(concrete) >= 6:
        positives.append(Signal(
            id="concrete_jd",
            severity="positive",
            title="Description contains concrete, verifiable detail",
            detail=f"Found {len(concrete)} specifics a template cannot fake: reporting "
                   f"lines, team size, deliverables, process, compensation. This is what "
                   f"a real requisition looks like.",
            source="VidCruiter (2026), jobsolv (2026)",
            weight=-15,
            evidence=", ".join(concrete[:6]),
        ))
    if dom and dom not in FREE_EMAIL_DOMAINS:
        positives.append(Signal(
            id="corp_email",
            severity="positive",
            title="Recruiter writes from a corporate domain",
            detail=f"{dom} is an owned domain, not a free mailbox.",
            source="FlexJobs (2026)",
            weight=-8,
        ))
    if salary_listed is True:
        positives.append(Signal(
            id="salary_listed",
            severity="positive",
            title="Compensation is disclosed",
            detail="Pay transparency is a strong marker of a live, budgeted requisition.",
            source="jobsolv (2026)",
            weight=-8,
        ))
    if ch in {"company_portal", "careers_page", "ats", "linkedin"}:
        positives.append(Signal(
            id="official_channel",
            severity="positive",
            title="Contact came through an official channel",
            detail=f"Application routed via {ch.replace('_', ' ')}, which is how real "
                   f"recruiting actually happens.",
            source="FlexJobs (2026)",
            weight=-10,
        ))

    signals.extend(positives)

    # ---- Score ---------------------------------------------------------
    total = sum(s.weight for s in signals)
    has_critical = any(s.severity == "critical" for s in signals)
    score = max(0, min(100, total))
    if has_critical:
        score = max(score, 88)

    if score >= 80:
        verdict: Verdict = "DANGER"
    elif score >= 60:
        verdict = "HIGH RISK"
    elif score >= 40:
        verdict = "CAUTION"
    elif score >= 20:
        verdict = "LOW RISK"
    else:
        verdict = "CLEAR"

    is_scam = has_critical
    ghost_ids = {"age_60", "age_30", "reposted", "vague_jd", "flooded_old", "no_salary"}
    ghost_weight = sum(s.weight for s in signals if s.id in ghost_ids and s.weight > 0)
    is_ghost = (not is_scam) and ghost_weight >= 25

    if is_scam:
        summary = (
            "Do not engage. This carries at least one fraud signal that no legitimate "
            "employer exhibits. Walk away and report it."
        )
    elif verdict == "DANGER":
        summary = (
            "Multiple stacked red flags. Treat as hostile until independently verified "
            "through a channel you found yourself."
        )
    elif verdict == "HIGH RISK":
        summary = (
            "Serious concerns. Verify the requisition exists on the company's own careers "
            "page before spending a minute tailoring."
        )
    elif verdict == "CAUTION":
        summary = (
            "Ambiguous. Probably a ghost rather than a scam — the risk is your time, not "
            "your money. Run the verification steps, then decide."
        )
    elif verdict == "LOW RISK":
        summary = "Minor flags only. Reasonable to apply; keep the usual guardrails up."
    else:
        summary = (
            "No meaningful red flags. This looks like a live requisition from a real "
            "employer. Spend your tailoring effort here."
        )

    return GhostReport(
        risk_score=score,
        verdict=verdict,
        is_probable_scam=is_scam,
        is_probable_ghost=is_ghost,
        signals=sorted(signals, key=lambda s: -abs(s.weight)),
        naira_at_risk=naira,
        hours_at_risk=0.75 if is_ghost else 0.0,
        verification_steps=_verification_steps(is_scam, is_ghost, company_name, company_website),
        summary=summary,
    )


def _verification_steps(is_scam: bool, is_ghost: bool, company: str, website: str) -> list[dict]:
    """Concrete next actions, drawn from the verification guidance in the research."""
    co = company or "the company"
    steps = [
        {
            "title": f"Search '{co} scam' and '{co} fake recruitment'",
            "why": "FlexJobs' own verification advice. Victim reports surface fast for "
                   "organisations that are being impersonated.",
            "minutes": 3,
            "critical": is_scam,
        },
        {
            "title": "Open the company's own careers page and search the exact job title",
            "why": "The single strongest ghost test. If the role is not on their own "
                   "portal, the third-party listing is stale, unofficial, or invented. "
                   "Type the address yourself; never follow their link.",
            "minutes": 2,
            "critical": True,
        },
        {
            "title": "Call the organisation on a number you found independently",
            "why": "Not the number in the message. Directory listings, LinkedIn, or their "
                   "official site.",
            "minutes": 10,
            "critical": is_scam,
        },
    ]
    if is_scam:
        steps.append({
            "title": "Never pay, never send ID, never share bank details",
            "why": "Payment demands are not negotiable in legitimate hiring. There is no "
                   "version of this where paying first is correct.",
            "minutes": 0,
            "critical": True,
        })
        steps.append({
            "title": "Report it",
            "why": "Nigerian Police Cybercrime Unit, the EFCC, or the job board's report "
                   "function. Reporting is how the next person is protected.",
            "minutes": 15,
            "critical": False,
        })
    if is_ghost:
        steps.append({
            "title": "Check the recruiter's recent LinkedIn activity",
            "why": "If the named recruiter has not posted or engaged with hiring content "
                   "in weeks, the role is not a priority for them right now.",
            "minutes": 5,
            "critical": False,
        })
        steps.append({
            "title": "If you get a screening call, ask: 'Who does this role report to, "
                       "and what is the first project?'",
            "why": "A hiring manager with a real req answers instantly and specifically. "
                   "Vague answers to concrete questions are the tell.",
            "minutes": 0,
            "critical": False,
        })
    if website:
        steps.append({
            "title": "Verify the domain character by character",
            "why": "Brand clones differ by one character (Payportepro vs PayPorté). Read "
                   "the whole string, do not skim it.",
            "minutes": 2,
            "critical": is_scam,
        })
    return steps
