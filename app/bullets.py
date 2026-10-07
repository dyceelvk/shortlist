"""
Bullet Lab - turns duty statements into evidence.

The Resume Genius 2026 report found the hardest parts of updating a resume are
"turning job duties into strong accomplishments" (35%) and "writing strong
bullet points" (32%). This module attacks exactly that.

It is deliberately NOT a text generator that invents achievements. Fabricated
metrics get people fired in their first month and, per the same report, 18% of
job seekers already admit to exaggerating results. Instead it:
  1. diagnoses what is weak about the bullet,
  2. picks an outcome verb matched to the domain,
  3. builds a fill-in-the-blank scaffold, and
  4. asks the specific question whose answer supplies the missing number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ats_match import ACTION_VERBS, DOMAIN_KEYWORDS, WEAK_STARTERS


@dataclass
class BulletFix:
    original: str
    problems: list[str] = field(default_factory=list)
    scaffold: str = ""
    domain: str = "default"
    verb_options: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    has_metric: bool = False
    word_count: int = 0

    def as_dict(self) -> dict:
        return {
            "original": self.original,
            "problems": self.problems,
            "scaffold": self.scaffold,
            "domain": self.domain,
            "verb_options": self.verb_options,
            "questions": self.questions,
            "has_metric": self.has_metric,
            "word_count": self.word_count,
        }


METRIC_PAT = re.compile(r"\d+(?:\.\d+)?\s?(?:%|percent|k|m|bn|x\b|hours?|days?|"
                        r"weeks?|months?|people|users?|clients?|accounts?|₦|\$|€|£)")

PASSIVE_HINTS = [" was ", " were ", " been ", " being ", "is responsible", "are responsible"]

METRIC_QUESTIONS = {
    "engineering": [
        "What got faster, smaller, or more reliable - and by how much?",
        "How many users, requests, or systems were affected?",
        "What broke before, and what is the incident/error rate now?",
        "How long did this take you versus the previous way of doing it?",
    ],
    "data": [
        "What decision did this analysis change, and what was the outcome?",
        "How much data, and how much faster does it move now?",
        "What was the error rate before versus after?",
        "What revenue or cost did the insight touch?",
    ],
    "operations": [
        "How many steps, hours, or people did you remove from the process?",
        "What did it cost before versus after?",
        "How many vendors, sites, or SKUs did this cover?",
        "What was the compliance or error rate before versus after?",
    ],
    "sales": [
        "What revenue did you close, and against what quota?",
        "How many accounts, and what size?",
        "How much did the cycle shorten?",
        "What was the win rate or retention before versus after?",
    ],
    "marketing": [
        "What moved - reach, conversion, CAC, or revenue - and by how much?",
        "What was the budget you delivered it on?",
        "Which channel, and what was the before/after number?",
        "What would not have happened without this campaign?",
    ],
    "leadership": [
        "How many people, and what did they go on to achieve?",
        "What did attrition or performance look like before versus after?",
        "How many did you hire, promote, or retain?",
        "What was the team delivering before versus after you took it over?",
    ],
    "finance": [
        "How much money - recovered, saved, or reconciled?",
        "How many entities, ledgers, or lines?",
        "How much faster did close happen?",
        "What exposure or error did you eliminate?",
    ],
    "default": [
        "What changed as a result, measured how?",
        "How many people, customers, or units were affected?",
        "What did this cost before versus after?",
        "What would have gone wrong without it?",
    ],
}


def detect_domain(text: str) -> str:
    t = (text or "").lower()
    scores = {d: sum(1 for k in words if k in t) for d, words in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else "default"


def fix_bullet(bullet: str) -> BulletFix:
    b = (bullet or "").strip()
    if not b:
        return BulletFix(original=b)

    clean = re.sub(r"^[\s\-•*▪–—]+\s*", "", b).strip()
    low = clean.lower()
    problems: list[str] = []

    starter = next((w for w in WEAK_STARTERS if low.startswith(w)), None)
    if starter:
        problems.append(
            f"Opens with \"{starter}\" - that phrase describes a job description, "
            f"not something you achieved. Recruiters read it as filler and skim past.")
    elif not re.match(r"^[a-z]+(?:ed|t|n)\b", low) and clean[:1].isupper():
        first = clean.split()[0] if clean.split() else ""
        if first.lower() not in {"led", "built", "owned", "drove", "grew", "cut"}:
            problems.append(
                f"Opens with \"{first}\". Strong bullets open with a past-tense outcome "
                f"verb that implies a result, not an activity.")

    has_metric = bool(METRIC_PAT.search(clean))
    if not has_metric:
        problems.append(
            "No number anywhere. This is the single most common weakness in resumes - "
            "a claim with no magnitude is indistinguishable from a lie, so recruiters "
            "discount it.")

    if any(h in f" {low} " for h in PASSIVE_HINTS):
        problems.append("Passive construction. Nobody did anything; something was done.")

    wc = len(clean.split())
    if wc > 30:
        problems.append(f"{wc} words. A recruiter spends 6-8 seconds per resume. "
                        f"Cut to 15-20.")
    elif wc < 5:
        problems.append(f"Only {wc} words - too thin to be credible evidence.")

    if re.search(r"\b(?:various|several|many|some|different|numerous)\b", low):
        problems.append("Vague quantifier (\"various\", \"several\"). Replace with the "
                        "actual count - you know it.")

    if not problems:
        problems.append("This one is already strong. Keep it and apply the same shape "
                        "to your weaker bullets.")

    domain = detect_domain(clean)
    verbs = ACTION_VERBS.get(domain, ACTION_VERBS["default"])

    scaffold = (
        f"[{verbs[0]}] [what you changed] by [number + unit], "
        f"[timeframe or scope], resulting in [business outcome]."
    )

    return BulletFix(
        original=b,
        problems=problems,
        scaffold=scaffold,
        domain=domain,
        verb_options=verbs[:6],
        questions=METRIC_QUESTIONS.get(domain, METRIC_QUESTIONS["default"])[:3],
        has_metric=has_metric,
        word_count=wc,
    )


def fix_resume_bullets(resume: str) -> list[BulletFix]:
    out: list[BulletFix] = []
    for line in (resume or "").splitlines():
        if re.match(r"^\s*[-•*▪–—]\s+\S", line):
            fx = fix_bullet(line)
            # Only surface the ones that actually need work.
            if fx.problems and not fx.has_metric or (fx.problems and len(fx.problems) > 1):
                out.append(fx)
    # Worst offenders first: most problems, then no metric.
    out.sort(key=lambda f: (f.has_metric, -len(f.problems)))
    return out[:12]
