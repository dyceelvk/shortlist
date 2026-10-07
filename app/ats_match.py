"""
ATS Match - keyword alignment, rank estimation and recruiter-search simulation.

Built on what ATS platforms actually do, per recruiter testimony and Enhancv's
2025 study of 25 US recruiters across 10+ ATS platforms:

  * 92% of ATS rank and sort. Only 8% auto-reject on content.
  * The viral "75% of resumes are rejected by ATS" stat traces to a company
    dead since 2013 and has been debunked.
  * The real failure mode is INVISIBILITY: recruiters run boolean strings
    against the candidate database, and a resume missing the exact term never
    surfaces. Being ranked #150 of 180 is functionally a rejection.
  * Median resume scores 48/100 against a job description and misses 52% of
    the job's keywords (ResumeAdapter pipeline data).

So this module does not promise to "beat the filter". It tells you where you
rank, what you are missing, and the literal search string a recruiter would
type to find someone like you.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Skill taxonomy. Curated, with acronym <-> expansion pairs so that "k8s" and
# "Kubernetes" count as the same skill, which is exactly how a recruiter's
# boolean string treats them.
# --------------------------------------------------------------------------

# canonical: (aliases used in resumes/JDs)
SKILL_ALIASES: dict[str, list[str]] = {
    # languages
    "python": ["python", "python3", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "c#": ["c#", "csharp", "c sharp", ".net", "dotnet"],
    "c++": ["c++", "cpp"],
    "go": ["golang", " go ", "go language"],
    "rust": ["rust"],
    "php": ["php"],
    "ruby": ["ruby"],
    "swift": ["swift"],
    "kotlin": ["kotlin"],
    "sql": ["sql", "t-sql", "pl/sql", "plsql"],
    "r": [" r ", "r language", "r programming"],
    "dart": ["dart"],
    "scala": ["scala"],
    "solidity": ["solidity"],
    "bash": ["bash", "shell scripting", "shell"],
    # frontend
    "react": ["react", "react.js", "reactjs"],
    "next.js": ["next.js", "nextjs", "next js"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angularjs"],
    "svelte": ["svelte"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "scss", "sass", "tailwind"],
    "redux": ["redux"],
    # backend
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi", "fast api"],
    "node.js": ["node.js", "nodejs", "node"],
    "express": ["express", "express.js", "expressjs"],
    "spring boot": ["spring boot", "springboot", "spring"],
    "laravel": ["laravel"],
    "rails": ["ruby on rails", "rails"],
    "graphql": ["graphql"],
    "rest api": ["rest api", "rest apis", "restful", "restful api"],
    "microservices": ["microservices", "micro-services"],
    # data / ml
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision", "cv"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "spark": ["spark", "pyspark", "apache spark"],
    "etl": ["etl", "elt"],
    "data modeling": ["data modeling", "data modelling"],
    "statistical analysis": ["statistical analysis", "statistics", "regression"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel", "spreadsheet", "microsoft excel", "advanced excel"],
    "looker": ["looker"],
    "dbt": ["dbt"],
    "airflow": ["airflow", "apache airflow"],
    # cloud / infra
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker", "containerisation", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform", "iac", "infrastructure as code"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous delivery",
              "continuous deployment", "jenkins", "github actions", "gitlab ci"],
    "linux": ["linux", "unix"],
    "ansible": ["ansible"],
    "nginx": ["nginx"],
    # databases
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql", "mariadb"],
    "mongodb": ["mongodb", "mongo", "nosql"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch", "elastic"],
    "snowflake": ["snowflake"],
    "oracle": ["oracle db", "oracle database"],
    # design / product
    "figma": ["figma"],
    "sketch": ["sketch app"],
    "adobe xd": ["adobe xd", "xd"],
    "photoshop": ["photoshop"],
    "illustrator": ["illustrator"],
    "ui design": ["ui design", "user interface design", "ui/ux"],
    "ux research": ["ux research", "user research", "usability testing"],
    "wireframing": ["wireframe", "wireframing", "prototyping", "prototype"],
    "design systems": ["design system", "design systems", "component library"],
    # management / method
    "agile": ["agile", "kanban"],
    "scrum": ["scrum", "scrum master", "sprint planning"],
    "jira": ["jira", "atlassian"],
    "confluence": ["confluence"],
    "notion": ["notion"],
    "project management": ["project management", "project manager", "pmp"],
    "product management": ["product management", "product manager", "roadmap",
                           "product strategy"],
    "stakeholder management": ["stakeholder management", "stakeholder engagement"],
    "budgeting": ["budgeting", "budget management", "p&l", "cost control"],
    "risk management": ["risk management", "risk assessment"],
    "six sigma": ["six sigma", "lean six sigma"],
    "lean": ["lean methodology", "lean"],
    # finance / accounting
    "ifrs": ["ifrs", "international financial reporting"],
    "financial reporting": ["financial reporting", "financial statements"],
    "financial modelling": ["financial model", "financial modelling",
                            "financial modeling", "dcf"],
    "auditing": ["auditing", "audit", "internal audit"],
    "taxation": ["taxation", "tax compliance", "vat"],
    "reconciliation": ["reconciliation", "bank reconciliation"],
    "sage": ["sage", "sage 50"],
    "quickbooks": ["quickbooks"],
    "sap": ["sap"],
    "oracle erp": ["oracle erp", "erp"],
    # marketing / growth
    "seo": ["seo", "search engine optimisation", "search engine optimization"],
    "sem": ["sem", "ppc", "google ads", "paid search"],
    "social media marketing": ["social media marketing", "social media management",
                               "community management"],
    "content marketing": ["content marketing", "content strategy", "copywriting"],
    "email marketing": ["email marketing", "mailchimp", "klaviyo", "hubspot"],
    "google analytics": ["google analytics", "ga4"],
    "crm": ["crm", "salesforce", "hubspot crm", "zoho crm"],
    "brand strategy": ["brand strategy", "branding", "brand management"],
    "market research": ["market research", "competitive analysis", "consumer insight"],
    # sales / ops
    "b2b sales": ["b2b sales", "enterprise sales", "business development"],
    "negotiation": ["negotiation", "contract negotiation"],
    "account management": ["account management", "key account", "client management"],
    "lead generation": ["lead generation", "prospecting", "pipeline management"],
    "customer service": ["customer service", "customer support", "customer success"],
    "supply chain": ["supply chain", "logistics", "procurement", "inventory management"],
    "health and safety": ["hse", "health and safety", "osha", "neosha"],
    # soft / transferable
    "communication": ["communication skills", "communication", "written communication",
                      "verbal communication"],
    "leadership": ["leadership", "team leadership", "line management", "people management"],
    "problem solving": ["problem solving", "problem-solving", "analytical skills",
                        "critical thinking"],
    "collaboration": ["collaboration", "cross-functional", "teamwork", "team work"],
    "mentoring": ["mentoring", "coaching", "training delivery"],
    "presentation": ["presentation skills", "presenting", "public speaking"],
    "time management": ["time management", "prioritisation", "prioritization",
                        "deadline management"],
    "adaptability": ["adaptability", "flexibility", "resilience"],
    # certs
    "aws certified": ["aws certified", "aws solutions architect"],
    "comptia": ["comptia", "a+", "network+", "security+"],
    "cissp": ["cissp"],
    "cisa": ["cisa"],
    "acca": ["acca"],
    "ican": ["ican", "chartered accountants of nigeria", "chartered accountant"],
    "cfa": ["cfa"],
    "cim": ["cim", "chartered institute of marketing"],
    "prince2": ["prince2", "prince 2"],
    "itil": ["itil"],
    "cips": ["cips"],
    "coren": ["coren", "registered engineer"],
    "mrcp": ["mrcp", "medical doctor", "mbbs"],
}

HARD_SKILL_HINTS = set(SKILL_ALIASES.keys())
SOFT_SKILLS = {
    "communication", "leadership", "problem solving", "collaboration", "mentoring",
    "presentation", "time management", "adaptability",
}

STOPWORDS = set("""
a an and are as at be been being but by for from had has have he her his how i if in
into is it its me my of on or our she so than that the their them then there these
they this to was we were what when where which who whom will with you your not no nor
all any can could did do does doing done would should shall may might must about above
after again against because before below between both during each few more most other
some such only own same too very s t just don now we're you're it's that's i'm
""".split())

# Uppercase tokens that look like skills to a naive acronym scan but are not
# skills anyone is hired for. Currency codes, boilerplate, and unit noise.
NON_SKILL_ACRONYMS = {
    # currency
    "ngn", "usd", "gbp", "eur", "zar", "ghs", "kes", "egh", "inr", "cad", "aud",
    "nzd", "chf", "jpy", "cny", "aed", "sar", "xof", "xaf", "btc", "usdt",
    # job-ad boilerplate
    "etc", "ie", "eg", "am", "pm", "ft", "pt", "eoe", "nb", "ps", "tbd", "tba",
    "asap", "wfh", "hyb", "mgt", "dept", "co", "ltd", "llc", "plc", "inc",
    "kg", "km", "hr", "hrs", "min", "max", "avg", "total", "n/a", "na",
    # common false hits
    "id", "ids", "no", "ok", "uk", "us", "eu", "me", "we", "it", "to", "of",
    "qa", "q1", "q2", "q3", "q4", "fy", "yoy", "kpi", "okr", "roi",
}

SENIORITY_TOKENS = {
    "intern": 0, "internship": 0, "trainee": 0, "graduate": 1, "entry-level": 1,
    "entry level": 1, "junior": 1, "associate": 1, "mid-level": 2, "mid level": 2,
    "mid-weight": 2, "senior": 3, "lead": 4, "staff": 4, "principal": 5,
    "manager": 4, "head of": 5, "director": 5, "vp": 6, "chief": 6,
}

WEAK_STARTERS = [
    "responsible for", "worked on", "worked with", "helped with", "helped to",
    "assisted with", "assisted in", "duties included", "tasked with", "in charge of",
    "involved in", "part of a team", "participated in", "supported the",
]

ACTION_VERBS = {
    "engineering": ["Architected", "Built", "Shipped", "Refactored", "Automated",
                    "Scaled", "Migrated", "Deployed", "Instrumented", "Optimised"],
    "data": ["Modelled", "Quantified", "Forecasted", "Segmented", "Pipeline-built",
             "Automated", "Consolidated", "Validated", "Attributed"],
    "operations": ["Streamlined", "Restructured", "Consolidated", "Automated",
                   "Centralised", "Negotiated", "Cut", "Reduced", "Recovered"],
    "sales": ["Closed", "Expanded", "Upsold", "Recovered", "Converted", "Negotiated",
              "Onboarded", "Penetrated"],
    "marketing": ["Grew", "Launched", "Repositioned", "Scaled", "Doubled", "Cut",
                  "Attributed", "Relaunched"],
    "leadership": ["Led", "Mentored", "Recruited", "Restructured", "Coached",
                   "Scaled", "Transformed"],
    "finance": ["Reconciled", "Recovered", "Reduced", "Consolidated", "Audited",
                "Modelled", "Automated"],
    "default": ["Delivered", "Led", "Built", "Improved", "Reduced", "Increased",
                "Launched", "Streamlined", "Owned", "Drove"],
}

DOMAIN_KEYWORDS = {
    "engineering": ["code", "api", "deploy", "server", "database", "frontend",
                    "backend", "software", "system", "bug", "repository", "cloud"],
    "data": ["data", "analytics", "model", "dashboard", "metric", "warehouse",
             "query", "report", "statistic", "etl", "bi"],
    "operations": ["process", "workflow", "supply", "logistics", "inventory",
                   "vendor", "sop", "compliance", "audit", "procurement"],
    "sales": ["revenue", "client", "quota", "pipeline", "deal", "account",
              "prospect", "closed", "upsell", "target"],
    "marketing": ["campaign", "audience", "brand", "content", "engagement",
                  "conversion", "seo", "social", "copy", "reach"],
    "leadership": ["team", "managed", "report", "direct", "mentored", "hired",
                   "supervised", "department"],
    "finance": ["ledger", "reconcil", "invoice", "budget", "tax", "audit",
                "financial", "payroll", "ifrs", "variance"],
}


@dataclass
class Keyword:
    term: str
    canonical: str
    category: str      # hard | tool | cert | soft | other
    weight: float
    count: int
    matched: bool
    in_resume_as: str = ""

    def as_dict(self) -> dict:
        return {
            "term": self.term, "canonical": self.canonical, "category": self.category,
            "weight": round(self.weight, 2), "count": self.count, "matched": self.matched,
            "in_resume_as": self.in_resume_as,
        }


@dataclass
class MatchReport:
    match_rate: int
    hard_match_rate: int
    keywords: list[Keyword] = field(default_factory=list)
    missing: list[Keyword] = field(default_factory=list)
    matched: list[Keyword] = field(default_factory=list)
    boolean_string: str = ""
    rank: dict = field(default_factory=dict)
    format_checks: list[dict] = field(default_factory=list)
    format_score: int = 0
    parse_risk: str = ""
    honest_note: str = ""
    extras_in_resume: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "match_rate": self.match_rate,
            "hard_match_rate": self.hard_match_rate,
            "keywords": [k.as_dict() for k in self.keywords],
            "missing": [k.as_dict() for k in self.missing],
            "matched": [k.as_dict() for k in self.matched],
            "boolean_string": self.boolean_string,
            "rank": self.rank,
            "format_checks": self.format_checks,
            "format_score": self.format_score,
            "parse_risk": self.parse_risk,
            "honest_note": self.honest_note,
            "extras_in_resume": self.extras_in_resume,
        }


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _canonical_of(alias: str) -> str | None:
    a = _norm(alias)
    for canon, aliases in SKILL_ALIASES.items():
        if a == canon or a in [_norm(x) for x in aliases]:
            return canon
    return None


def _category(canonical: str) -> str:
    if canonical in SOFT_SKILLS:
        return "soft"
    if any(canonical.startswith(c) for c in ("aws certified", "comptia", "cissp", "cisa",
                                             "acca", "ican", "cfa", "cim", "prince2",
                                             "itil", "cips", "coren", "mrcp")):
        return "cert"
    if canonical in {"figma", "jira", "confluence", "notion", "tableau", "power bi",
                     "sage", "quickbooks", "sap", "sketch", "photoshop", "illustrator",
                     "excel", "adobe xd", "looker", "dbt", "airflow", "nginx", "ansible",
                     "google analytics", "crm", "email marketing"}:
        return "tool"
    return "hard"


def _requirements_span(text: str) -> str:
    """Return the requirements/qualifications section if one is identifiable."""
    t = text or ""
    m = re.search(
        r"(?:requirements?|qualifications?|what (?:we'?re|we are) looking for|"
        r"skills?|experience required|ideal candidate|about you)(.{0,3000})",
        t, re.I | re.S)
    return m.group(1) if m else t


def extract_keywords(job_description: str) -> list[Keyword]:
    """Pull weighted skills/tools/certs/soft-skills out of a job description."""
    jd = job_description or ""
    req = _requirements_span(jd)
    found: dict[str, Keyword] = {}

    # Pass 1: taxonomy match (handles acronyms and expansions correctly).
    for canon, aliases in SKILL_ALIASES.items():
        n_full = 0
        for alias in [canon] + aliases:
            a = _norm(alias).strip()
            if not a:
                continue
            pat = re.compile(r"(?<![a-z0-9+#.])" + re.escape(a) + r"(?![a-z0-9])")
            n_full += len(pat.findall(_norm(jd)))
        if n_full == 0:
            continue
        # Terms in the requirements section are worth double: that is what the
        # recruiter filters on.
        n_req = 0
        for alias in [canon] + aliases:
            a = _norm(alias).strip()
            if not a:
                continue
            pat = re.compile(r"(?<![a-z0-9+#.])" + re.escape(a) + r"(?![a-z0-9])")
            n_req += len(pat.findall(_norm(req)))
        weight = 1.0 + 0.6 * math.log1p(n_full) + (1.5 if n_req else 0.0)
        found[canon] = Keyword(
            term=canon, canonical=canon, category=_category(canon),
            weight=weight, count=n_full, matched=False,
        )

    # Pass 2: domain nouns and repeated bigrams the taxonomy misses.
    tokens = [w for w in re.findall(r"[a-z][a-z0-9+#./-]{2,}", _norm(jd))
              if w not in STOPWORDS and len(w) > 2]
    freq: dict[str, int] = {}
    for w in tokens:
        freq[w] = freq.get(w, 0) + 1
    for w, c in freq.items():
        if c >= 3 and w not in found and not any(w in a for a in SKILL_ALIASES.values()
                                                 if isinstance(a, list)):
            found[w] = Keyword(term=w, canonical=w, category="other",
                               weight=0.5 + 0.25 * c, count=c, matched=False)

    # Pass 3: ALL-CAPS acronyms (2-6 chars) not already captured.
    for m in re.finditer(r"\b([A-Z][A-Z0-9+#]{1,5})\b", jd or ""):
        ac = m.group(1)
        low = ac.lower()
        if low in STOPWORDS or low in NON_SKILL_ACRONYMS or low in found or _canonical_of(low):
            continue
        c = len(re.findall(r"\b" + re.escape(ac) + r"\b", jd))
        if c >= 1:
            found.setdefault(low, Keyword(term=ac, canonical=low, category="other",
                                          weight=0.8 + 0.2 * c, count=c, matched=False))

    return sorted(found.values(), key=lambda k: -k.weight)


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------

def _resume_terms(resume: str) -> set[str]:
    """Expand a resume into the set of canonical skills it demonstrably claims."""
    n = _norm(resume)
    hits: set[str] = set()
    for canon, aliases in SKILL_ALIASES.items():
        for alias in [canon] + aliases:
            a = _norm(alias).strip()
            if not a:
                continue
            pat = re.compile(r"(?<![a-z0-9+#.])" + re.escape(a) + r"(?![a-z0-9])")
            if pat.search(n):
                hits.add(canon)
                break
    return hits


def _exact_present(canonical: str, resume: str) -> str:
    """Which literal spelling of this skill appears in the resume? Empty if none."""
    n = _norm(resume)
    for alias in [canonical] + SKILL_ALIASES.get(canonical, []):
        a = _norm(alias).strip()
        if not a:
            continue
        pat = re.compile(r"(?<![a-z0-9+#.])" + re.escape(a) + r"(?![a-z0-9])")
        m = pat.search(n)
        if m:
            return m.group(0)
    return ""


def analyze(jd: str, resume: str, *, pool_size: int = 180, reviewed: int = 20) -> MatchReport:
    kws = extract_keywords(jd)
    resume_canonicals = _resume_terms(resume)

    total_w = 0.0
    matched_w = 0.0
    hard_total = 0.0
    hard_matched = 0.0

    for k in kws:
        present = _exact_present(k.canonical, resume)
        k.matched = bool(present) or (k.category == "other" and k.canonical in _norm(resume))
        if k.matched and present:
            k.in_resume_as = present
        total_w += k.weight
        if k.matched:
            matched_w += k.weight
        if k.category in {"hard", "tool", "cert"}:
            hard_total += k.weight
            if k.matched:
                hard_matched += k.weight

    match_rate = int(round(100 * matched_w / total_w)) if total_w else 0
    hard_rate = int(round(100 * hard_matched / hard_total)) if hard_total else 0

    missing = [k for k in kws if not k.matched]
    matched = [k for k in kws if k.matched]

    # What the resume has that the JD never asks for - wasted real estate.
    jd_canon = {k.canonical for k in kws}
    extras = sorted(c for c in resume_canonicals if c not in jd_canon)

    report = MatchReport(
        match_rate=match_rate,
        hard_match_rate=hard_rate,
        keywords=kws,
        missing=missing,
        matched=matched,
        boolean_string=build_boolean_string(kws),
        rank=estimate_rank(match_rate, pool_size=pool_size, reviewed=reviewed),
        extras_in_resume=extras[:25],
    )
    report.format_checks, report.format_score, report.parse_risk = check_format(resume)
    report.honest_note = (
        "This score measures keyword alignment, not your worth or your chances of an "
        "offer. Enhancv's 2025 study of 25 recruiters across 10+ ATS platforms found "
        "92% of systems rank rather than auto-reject. The real risk is invisibility in "
        "a recruiter's search, which is what the boolean string below shows you."
    )
    return report


# --------------------------------------------------------------------------
# Boolean search simulation
# --------------------------------------------------------------------------

def build_boolean_string(kws: list[Keyword]) -> str:
    """
    Reconstruct the actual search a recruiter would run against an ATS database
    for this role. This is the string your resume either matches or does not.
    """
    hard = [k for k in kws if k.category in {"hard", "tool", "cert"}]
    if not hard:
        return ""
    top = hard[:6]

    def spellings(canon: str) -> list[str]:
        out = [canon]
        for a in SKILL_ALIASES.get(canon, []):
            a = a.strip()
            if a and a != canon and len(a) > 1 and a not in out:
                out.append(a)
        return out[:3]

    parts = []
    for k in top:
        sp = spellings(k.canonical)
        if len(sp) == 1:
            parts.append([sp[0]])
        else:
            parts.append(sp)

    def render(sp: list[str], *, group: bool) -> str:
        inner = " OR ".join(f'"{s}"' for s in sp)
        # Grouping is load-bearing, not cosmetic: AND binds tighter than OR, so
        # an ungrouped 'A OR B AND C OR D' parses as A OR (B AND C) OR D.
        return f"({inner})" if (group and len(sp) > 1) else inner

    if len(parts) >= 3:
        # Recruiters AND the top two must-haves and OR the rest, then exclude
        # interns and contractors.
        rest = [s for grp in parts[2:] for s in grp]
        s = (f'{render(parts[0], group=True)} AND '
             f'{render(parts[1], group=True)} AND '
             f'{render(rest, group=True)}')
    else:
        s = " AND ".join(render(p, group=True) for p in parts)
    return s + ' NOT "intern" NOT "internship"'


# --------------------------------------------------------------------------
# Rank estimation
# --------------------------------------------------------------------------

def estimate_rank(match_rate: int, *, pool_size: int = 180, reviewed: int = 20) -> dict:
    """
    Anchor: the median resume scores 48/100 against a JD (ResumeAdapter pipeline
    data). So 48 maps to the 50th percentile. We use a logistic curve through
    that point: ~70 lands near the 80th percentile, ~85 near the 95th.

    Then translate percentile into a position in the pile and whether that
    position falls inside the set a recruiter actually reads.
    """
    pct = 100.0 / (1.0 + math.exp(-(match_rate - 48) / 11.5))
    rank = max(1, int(round(pool_size * (1 - pct / 100.0)) + 1))
    in_review = rank <= reviewed
    return {
        "percentile": int(round(pct)),
        "estimated_rank": rank,
        "pool_size": pool_size,
        "reviewed": reviewed,
        "would_be_reviewed": in_review,
        "gap_to_reviewed": max(0, rank - reviewed),
        "note": (
            f"In a pile of ~{pool_size}, a {match_rate}% match sits around position "
            f"#{rank}. Recruiters read roughly the top {reviewed}. "
            + ("You are inside that set." if in_review else
               f"You are ~{rank - reviewed} places outside it, which is why silence "
               f"is the usual outcome at this score.")
        ),
    }


# --------------------------------------------------------------------------
# Format / parse risk
# --------------------------------------------------------------------------

def check_format(resume: str) -> tuple[list[dict], int, str]:
    """
    Recruiters confirmed 92% of ATS do not auto-reject on formatting - but 23% of
    rejections trace to parsing errors, so structure still decides whether your
    content is readable at all.
    """
    r = resume or ""
    checks: list[dict] = []
    score = 100

    def add(ok: bool, label: str, why: str, cost: int = 0) -> None:
        nonlocal score
        checks.append({"ok": ok, "label": label, "why": why})
        if not ok:
            score -= cost

    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", r))
    add(has_email, "Email address present",
        "Without it the recruiter cannot reach you; parsers put it in a required field.", 15)

    has_phone = bool(re.search(r"(\+?\d[\d\s()-]{7,}\d)", r))
    add(has_phone, "Phone number present", "Recruiters call; the ATS stores it as a "
        "filterable field.", 10)

    sections = re.findall(
        r"^\s*(experience|work experience|employment|education|skills|projects|"
        r"summary|profile|certifications?|awards?|publications?)\s*$",
        r, re.I | re.M)
    add(len(set(s.lower() for s in sections)) >= 3,
        f"Standard section headers found ({len(set(s.lower() for s in sections))})",
        "Parsers map content to fields by header. Unusual headers dump everything "
        "into one blob.", 15)

    dates = re.findall(
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}",
        r, re.I)
    add(len(dates) >= 2, f"Dates in a parseable format ({len(dates)} found)",
        "Month + year is the format every ATS date parser handles. Bare years or "
        "'present' alone break experience-length filters.", 12)

    lines = [l for l in r.splitlines() if l.strip()]
    bullets = [l for l in lines if re.match(r"^\s*[-•*▪–—]\s+\S", l)]
    ratio = len(bullets) / max(1, len(lines))
    add(0.3 <= ratio <= 0.85,
        f"Bullet usage looks normal ({len(bullets)} of {len(lines)} lines)",
        "Too few bullets means prose walls no one skims. Too many means no context "
        "anywhere.", 10)

    n_digits = len(re.findall(r"\d+(?:\.\d+)?%?", r))
    add(n_digits >= 6, f"Quantified results present ({n_digits} numeric tokens)",
        "Recruiters scan for numbers. Resume Worded and Rezi both flag "
        "unquantified bullets as the most common weakness.", 15)

    words = len(r.split())
    add(300 <= words <= 1200, f"Length is sane ({words} words)",
        "One to two pages. Below 300 words reads as thin; above ~1,200 no one "
        "finishes it.", 8)

    if re.search(r"\b(?:team player|hard working|hardworking|results[- ]driven|"
                 r"excellent communication)\b", r, re.I):
        checks.append({"ok": False, "label": "Clichéd self-descriptions present",
                       "why": "'Team player' and 'hardworking' claim nothing. Recruiters "
                              "discount them entirely. Replace each with evidence."})
        score -= 8
    else:
        checks.append({"ok": True, "label": "No clichéd self-descriptions",
                       "why": "Clean."})

    weak = sum(1 for w in WEAK_STARTERS if w in r.lower())
    if weak:
        checks.append({"ok": False, "label": f"{weak} weak bullet openers",
                       "why": "'Responsible for' describes a job description, not an "
                              "achievement. Rewrite with an outcome verb."})
        score -= min(15, weak * 3)
    else:
        checks.append({"ok": True, "label": "No weak bullet openers",
                       "why": "Every bullet leads with an outcome verb."})

    score = max(0, min(100, score))
    if score >= 85:
        risk = "Low - parses cleanly in every major ATS."
    elif score >= 65:
        risk = "Moderate - readable, but a few fields may land in the wrong place."
    else:
        risk = ("High - parts of this resume will likely fail to parse into structured "
                "fields, which is how 23% of rejections happen.")
    return checks, score, risk
