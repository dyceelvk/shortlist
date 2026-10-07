# Research dossier

The global sweep that produced SHORTLIST. Every rule in the code traces to a source
listed here. Research conducted 7 October 2026.

---

## 1. How I picked the niche

I surveyed five candidate markets before committing. The decision rule was:
**acute + frequent pain, demonstrated willingness to pay, buildable by one person,
and a visible gap the incumbents have not filled.**

| Candidate | Verdict |
|---|---|
| Job search / hiring | **Chosen.** Largest measurable pain, worst-served fraud problem, incumbents all priced for US wallets. |
| SME finance / invoicing | Crowded (Paystack, Flutterwave, Kuda, Wave all adjacent). Hard to differentiate solo. |
| Health & wellness | Strong revenue, but trust and liability barriers are too high for a v1. |
| Agriculture / food supply | Real pain, but needs physical operations and local logistics. Not a software-only v1. |
| Education / exam prep | Massive Nigerian market, but extremely crowded and monetises poorly per user. |

---

## 2. The pain, quantified

### Ghosting is the number-one frustration — for three years running
- **57.5%** of job seekers say applying and not hearing back is a top challenge —
  the #1 response for the third consecutive year. *(iHire, State of Online Recruiting 2026)*
- **55%** name it their single biggest frustration. *(Resume Genius 2026, n=1,000)*
- **77%** have been ghosted after applying since 2020; **61%** after interviews,
  up 9 points since early 2024. *(CoverSentry ATS Statistics 2026)*
- Most ghosting happens at the resume-drop point: **28%** after submitting an
  application, **20%** after one interview, **16%** after a phone screen. *(fastapply, n=1,024)*

### Fraud is endemic and nobody is solving it
- **41.2%** of job seekers encountered a fake or scam job in the past year.
- **39.3%** struggle with fake, fraudulent or "ghost" jobs.
- **42.8%** cannot tell whether a job or employer on a board is legitimate.
  *(all iHire 2026)*
- **67%** have suspected a posting of being fake or misleading. *(Resume Genius 2026)*
- **81%** of recruiters admit their employer posts ghost jobs; **18–22%** of jobs on
  the Greenhouse platform in any quarter are ghost jobs.
- Estimates of the ghost share of listings range from **one in seven to one in four**.
  *(jobsolv 2026)*
- Roughly **one in three** listings leads nowhere. *(job200, Huntr Q1 2026, 240,000 applications)*

### The cost is psychological, not just temporal
- **49%** say job searching is hurting their mental health.
- **36%** have considered "skills manifesting" — putting skills on a resume they
  do not have. *(Resume Genius 2026)*

### Nigeria specifically
- **600,000–1.7M** graduates enter a saturated market each year.
- Fewer than **20%** of graduates are immediately employable. *(AfDB)*
- **93%** of the workforce is informal; underemployment **25.8%**.
- **70%+** of employers report difficulty filling roles — a relevance gap, not a
  scarcity gap.
- Documented fraud losses: **₦20,000** (application service), **₦50,000**
  ("documentation"), **₦150,000** (fake business courses sold as a second screening
  round), **₦350,000** ("government agency connection"). Police arrested a man over a
  **₦40M** job scam in Kano, 2026. *(NewsClick NG; Peoples Gazette; Punch NG;
  Recruitment Boss NG 2026)*
- Transnational task scams ("review products, upgrade to withdraw") use deliberate
  early payouts to lower suspicion before the large deposit. *(Punch NG 2026)*

---

## 3. The science, corrected

**The most repeated claim in this industry is false.** "75% of resumes are rejected
by ATS before a human sees them" traces to a company out of business since 2013 and
has been debunked by HR professionals.

What is actually true:
- **92%** of recruiters confirmed their ATS does **not** auto-reject on content,
  formatting or design. Only **8%** are configured to. *(Enhancv 2025, 25 US
  recruiters across 10+ ATS platforms)*
- **100%** use knockout questions (work authorisation, certifications).
- ATS is a **database with a search interface**. Recruiters run boolean strings
  against it. A resume missing the exact term simply never surfaces.
- Being ranked **#150 of 180** is functionally identical to being rejected.
- **23%** of rejections trace to parsing errors, **12%** to formatting, **8%** to
  arbitrary knockout filters — only **57%** to actual qualification mismatch.
  *(CoverSentry 2026)*
- Median resume scores **48/100** against a job description and misses **52%** of the
  job's keywords. *(ResumeAdapter pipeline data)*

**The design consequence:** the honest product promise is not "beat the filter".
It is *"stop being invisible in the search."* That is why SHORTLIST shows you the
literal boolean string a recruiter would type.

---

## 4. The highest-ROI ignored lever

- Following up within **1–2 weeks** correlates with roughly a **20% lift** in callback
  rates. *(Resume Worded, n=1,200)*
- **57%** of job seekers never follow up at all.
- Documented individual case: **13.85%** response rate (65 applications, 9 responses)
  without follow-up vs **50%** (12 applications, 6 responses) with it.
  *(r/cscareerquestions)*

Timing that works:
| Stage | Wait |
|---|---|
| Online application | 5–7 business days |
| Phone screen | 3–5 business days |
| Interview | Thank-you within 24–48h, then a fuller check-in at 1–2 weeks |
| Assume cold | 14–21 days of silence |

Channel response rates:
| Channel | Rate |
|---|---|
| Direct recruiter email | 12–25% |
| LinkedIn InMail | 25–35% cold |
| Connection request + note | 15–30% accept |
| Phone | low connect, high impression |
| Application portal | **~0% — write-only** |
| Social DM | near zero, reads unprofessional |

---

## 5. The competitive gap

| Tool | Price | Free tier | Solves fraud? |
|---|---|---|---|
| Jobscan | $49.95/mo | 5 scans/mo | **No** |
| Teal | $29/mo ($9/wk) | ~90% of features | **No** |
| Rezi | $29/mo, $149 lifetime | 1 resume | **No** |
| Kickresume | $24/mo ($8/mo annual) | ATS checker is paid | **No** |
| Enhancv | — | limited | **No** |
| Resume Worded | free tier | generous | **No** |
| SkillSyncer | $14.95/mo | .edu/.mil free | **No** |

**Three gaps, all open:**

1. **Nobody detects fraud or ghost jobs.** It is the #2 pain globally (39–41%) and an
   existential one in Nigeria, and not one resume tool addresses it. The one partial
   exception is HideJobs, which filters by posting age only.
2. **Priced for US wallets.** $29–50/month is roughly ₦45,000–₦78,000/month. Absurd
   for the market with the most acute need.
3. **Nobody automates the chase.** Every tool ends at "your resume is optimised".
   None schedule or write the follow-up — the single cheapest, highest-return action
   available.

---

## 6. Ghost & scam signals used in the engine

**Fraud (money or identity theft):**
1. Any payment demand — registration, processing, forms, medicals, uniform,
   induction, training, visa, "secure your slot". The absolute line.
2. Payment to a personal account rather than Remita/corporate.
3. "Already shortlisted" / "connection inside" claims.
4. Task schemes — review products, like videos, subscribe, referral codes,
   "upgrade to withdraw". Early payouts are deliberate bait.
5. Manufactured urgency — "within 10 minutes", "today only", "limited slots".
6. Too-good-to-be-true — high pay + no experience + no interview.
7. Chat-first recruiting (WhatsApp/Telegram/IG) from a personal number.
8. Unsolicited contact from an unknown number.
9. Free email domain (gmail/yahoo/hotmail) for a corporate recruiter.
10. Brand-clone domains — `nnpc-career.com`, `fcsc-recruitment.ng`,
    `Payportepro` vs `PayPorté`.
11. Government body named on a non-`.gov.ng` domain.
12. No live interview of any kind.

**Ghost (real company, no real requisition):**
1. Listing 30+ days old; 60+ is high risk. Real roles fill in 30–60 days.
2. Repeatedly reposted with a reset date.
3. Vague JD — buzzword-dense, no reporting line, team size, deliverables or
   first project.
4. No compensation disclosed.
5. Not present on the company's own careers page.
6. "Over 100 applicants" on an old listing.
7. Automated rejection within hours of applying.

**Verification, in order of value:**
1. Open the company's own careers page and search the exact title (60 seconds,
   strongest single test).
2. Search "`company` scam".
3. Call a number you found independently, never the one in the message.
4. Check the named recruiter's recent LinkedIn activity.
5. Ask: "Who does this role report to, and what is the first project?" A hiring
   manager with a real req answers instantly and specifically.

---

## Sources

- iHire — *The State of Online Recruiting 2026*
- Resume Genius — *2026 Job Seeker Insights Report* (n=1,000)
- Enhancv — 2025 recruiter study (n=25, 10+ ATS platforms)
- Resume Worded — follow-up study (n=1,200)
- ResumeAdapter — ATS glossary & pipeline data
- CoverSentry — *ATS Statistics 2026*
- FlexJobs — *30 Job Scams to Watch for in 2026*
- VidCruiter — *Fake and Ghost Jobs* (2026)
- HideJobs — *Ghost Jobs: What They Are* (2026)
- jobsolv — *Ghost Jobs: How to Spot Them* (2026)
- job200 / Huntr — Q1 2026 study of 240,000 applications
- fastapply — *Why Am I Not Hearing Back* (n=1,024)
- Recruitment Boss NG — *Top 5 Recruitment Scams in Nigeria, 2026 Edition*
- Punch NG — *How Nigerians Fall Victim to Transnational Remote Job Scams* (2026)
- NewsClick NG — *Fake vacancies, job slots for sale, recruitment scams* (2026)
- Peoples Gazette — *Police arrest man over alleged N40 million job scam in Kano* (2026)
- Guardian NG, BusinessDay NG, Afrobarometer AD998, Daily Trust — Nigerian labour market
