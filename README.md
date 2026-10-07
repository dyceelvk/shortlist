# SHORTLIST

**Know if the job is real. Then get on the shortlist.**

57.5% of job seekers say being ghosted is their number-one frustration — for the
third year running. 41% have hit an outright scam job. In Nigeria, people lose
₦20,000 to ₦500,000 to recruiters who simply ask them to pay first.

Every existing tool optimises your resume. **None of them tell you whether the job
is real.** That is the gap SHORTLIST fills.

---

## The workflow

```
1. GHOST RADAR   →  is this job even real?        (run this FIRST)
2. ATS MATCH     →  where do you actually rank?
3. BULLET LAB    →  turn duties into evidence
4. FOLLOW-UP     →  run the chase that lifts callbacks ~20%
5. PIPELINE      →  track it all, see the money you didn't lose
```

Step 1 is the point. A ghost job costs you 45 minutes of tailoring. A scam costs
you money. Optimising a resume for a job that does not exist is pure loss — so
SHORTLIST makes you vet before you tailor.

---

## What it does that nothing else does

### Ghost Radar
A weighted, fully-sourced risk engine scoring 0–100 across 12 fraud signals and 7
ghost signals. Every fired signal carries a human-readable reason **and its source**.

Payment demands are treated as an absolute line, not a weighted factor — no
legitimate employer on earth charges a candidate to be hired. One payment signal
caps the verdict in DANGER on its own.

It also separates **ghost** from **scam**, because the remedy differs: a ghost costs
time, a scam costs money.

It catches:
- "Send ₦150,000 processing fee to my account" → DANGER 100
- Brand clones: `nnpc-career.com`, `fcsc-recruitment.ng`, `Payportepro` vs `PayPorté`
- Government impersonation on a non-`.gov.ng` domain
- Task schemes ("review products, upgrade to withdraw")
- "Already shortlisted" / "connection inside"
- Manufactured urgency, chat-first recruiting, no live interview
- Stale, reposted, buzzword-only ghost postings

And it does **not** flag clean postings. Word-boundary matching means "firs" inside
"**firs**t project" cannot trigger the FIRS impersonation rule.

### ATS Match — honest, not snake oil
The viral "75% of resumes are rejected by ATS" stat traces to a company dead since
2013. Enhancv's 2025 study of 25 recruiters across 10+ platforms found **92% of ATS
rank rather than auto-reject**. The real failure mode is **invisibility**: recruiters
run boolean strings against the database, and a resume missing the exact term never
surfaces.

So SHORTLIST gives you:
- Weighted match rate, hard-skills rate, and missing terms in priority order
- **The literal boolean string a recruiter would type** — copy it and search your own
  resume. Anything absent is a term you are invisible to.
- **Rank estimation**: in a pile of ~180, a 48% match (the documented median) sits at
  position ~#90. Recruiters read the top ~20. It tells you whether you are inside
  that set.
- Parse/format safety, because 23% of rejections trace to parsing errors

### Bullet Lab
35% of job seekers say turning duties into achievements is the hardest part of
updating a resume. This diagnoses each bullet — weak opener, no metric, passive
voice, vague quantifier — picks an outcome verb matched to the detected domain, and
asks **the specific question whose answer supplies the missing number**.

It deliberately does not invent achievements. Fabricated metrics get people fired,
and 18% of job seekers already admit to exaggerating results.

### Follow-up Autopilot
Following up within 1–2 weeks correlates with a ~20% callback lift. 57% never do it.
This computes a real business-day schedule and writes the emails.

If the recruiter gave you a timeline, the first chase is **deferred past it** —
chasing inside a window they asked you to respect reads as impatience. It parses
"three weeks", "2 weeks", "10 days", "a month", and degrades safely on anything it
cannot parse.

---

## Run it

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

Interactive docs at `/docs`.

## Test it

```bash
python -m pytest tests/ -q
# 76 passed
```

The suite covers the engines directly, including regressions for bugs found during
development: the substring agency match, the TLD-stripped `.gov.ng` test, the
`split(":")` URL bug, the `meta`/`metamorph` boundary bug, currency codes being read
as skills, boolean operator precedence, and the follow-up offset/date mismatch.

---

## Architecture

```
app/
  ghost_radar.py   fraud + ghost detection engine (weighted, sourced)
  ats_match.py     keyword taxonomy, match rate, rank model, boolean simulation
  bullets.py       bullet diagnosis and evidence scaffolds
  followup.py      business-day scheduler and email generation
  models.py        pydantic schemas
  main.py          FastAPI routes + pipeline persistence
static/            frontend (no external dependencies — works offline)
tests/             76 tests
```

No external API keys. No LLM calls. The engines are deterministic, so a score means
the same thing every time and every rule is auditable.

---

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/ghost` | Score a posting or recruiter message |
| POST | `/api/match` | Match rate, rank, missing keywords, boolean string |
| POST | `/api/bullets` | Diagnose weak bullets |
| POST | `/api/followup` | Dated chase schedule + written emails |
| GET/POST/PATCH/DELETE | `/api/pipeline` | Track applications |
| GET | `/api/health` | Liveness |

---

## Pricing thesis

Jobscan is $49.95/mo, Teal $29/mo, Rezi $29/mo. That is roughly ₦45,000–₦78,000/month
in the market with the most acute need and the worst fraud problem.

SHORTLIST's free tier should be genuinely unlimited on Ghost Radar — fraud detection
is a public good and the growth loop is a screenshot of a ₦150,000 scam caught. Paid
tier is the pipeline and unlimited match scans, priced for local purchasing power.

---

## What is deliberately not here

- **No auto-apply.** Mass application sprays your resume at dead requisitions and
  makes you part of the noise recruiters complain about.
- **No AI-generated achievements.** See above.
- **No scraping of job boards.** Fragile, and legally messy.

---

## Limits

Ghost Radar gives you evidence, not a verdict on a specific employer. A clean score
does not guarantee a real job; a red score does not prove intent to defraud. Verify
independently before acting. Nothing here is legal advice.

Keyword matching measures language alignment, not your worth or your chances of an
offer. The rank model is a calibrated estimate anchored to the documented median
(48/100 → 50th percentile), not a prediction about any specific employer.

See [RESEARCH.md](RESEARCH.md) for the full dossier and every source.
