"""
Follow-up Autopilot - the highest-ROI, most-ignored lever in job searching.

Evidence:
  * A Resume Worded study of 1,200 job seekers found following up within 1-2
    weeks of applying correlated with roughly a 20% lift in callback rates.
  * 57% of job seekers never follow up at all.
  * Documented individual case: response rate 13.85% (65 applications, 9
    responses) without follow-up vs 50% (12 applications, 6 responses) with it.
  * Timing that works: 5-7 business days after an online application; 3-5
    business days after a phone screen; thank-you within 24-48h of an
    interview, then a fuller check-in at 1-2 weeks.
  * Channel response rates: direct recruiter email 12-25%, LinkedIn InMail
    25-35%, connection request 15-30% accept, phone low-connect/high-impression,
    application portals effectively 0%, social DMs near 0 and unprofessional.
  * 14-21 days of silence means the trail has gone cold; close it gracefully
    and move on rather than chasing.

This module computes a real dated schedule using business days and writes the
actual emails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

WEEKEND = {5, 6}  # Saturday, Sunday


def add_business_days(start: date, n: int) -> date:
    d = start
    added = 0
    while added < n:
        d += timedelta(days=1)
        if d.weekday() not in WEEKEND:
            added += 1
    return d


def business_days_between(a: date, b: date) -> int:
    """Count business days from a to b (0 if same day, negative if b precedes a)."""
    if a == b:
        return 0
    sign = 1 if b > a else -1
    lo, hi = (a, b) if b > a else (b, a)
    n, d = 0, lo
    while d < hi:
        d += timedelta(days=1)
        if d.weekday() not in WEEKEND:
            n += 1
    return sign * n


_WORD_NUM = {
    "a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "fortnight": 14,
}


def _parse_timeline_days(text: str) -> int | None:
    """Turn 'three weeks' / '2 weeks' / '10 days' / 'a month' into a day count."""
    t = (text or "").lower()
    if not t.strip():
        return None
    m = re.search(r"(\d+)\s*(day|week|month|fortnight)", t)
    n = int(m.group(1)) if m else None
    if n is None:
        m = re.search(r"\b([a-z]+)\s*(day|week|month|fortnight)", t)
        if not m:
            return None
        n = _WORD_NUM.get(m.group(1))
        if n is None:
            return None
    unit = m.group(2)
    if unit.startswith("week") or unit == "fortnight":
        return n * 14 if unit == "fortnight" else n * 7
    if unit.startswith("month"):
        return n * 30
    return n


CHANNELS = [
    {
        "channel": "Direct email to the recruiter or hiring manager",
        "response_rate": "12-25%",
        "use_when": "You found a real named address and the posting does not forbid email.",
        "avoid_when": "Posting says 'no emails', or you only have a generic info@ box.",
        "rank": 1,
    },
    {
        "channel": "LinkedIn InMail",
        "response_rate": "25-35% on cold messages",
        "use_when": "No email available and the recruiter is active on LinkedIn.",
        "avoid_when": "You already have a working email - email is cheaper and faster.",
        "rank": 2,
    },
    {
        "channel": "LinkedIn connection request with a note",
        "response_rate": "15-30% accept, lower reply",
        "use_when": "You want the relationship to outlive this one role.",
        "avoid_when": "You are in a hurry or they log in weekly.",
        "rank": 3,
    },
    {
        "channel": "Phone call",
        "response_rate": "Low connect rate, high impression if you reach them",
        "use_when": "You have a direct line and you are confident on the phone.",
        "avoid_when": "Posting says 'no calls', or it is a large enterprise.",
        "rank": 4,
    },
    {
        "channel": "Application portal status check",
        "response_rate": "~0% - portals are write-only for candidates",
        "use_when": "Never as a follow-up. Use it to confirm receipt only.",
        "avoid_when": "Always as a conversation channel.",
        "rank": 5,
    },
    {
        "channel": "X / Instagram / other social DM",
        "response_rate": "Very low, reads as unprofessional",
        "use_when": "Only creative, social, or dev-rel roles where the hiring manager "
                    "is publicly active there.",
        "avoid_when": "Default. Stick to email and LinkedIn.",
        "rank": 6,
    },
]


@dataclass
class Step:
    label: str
    day: date
    offset_business_days: int
    subject: str
    body: str
    channel: str
    rationale: str

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "date": self.day.isoformat(),
            "date_human": self.day.strftime("%a %d %b %Y"),
            "offset_business_days": self.offset_business_days,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "rationale": self.rationale,
        }


@dataclass
class FollowUpPlan:
    stage: str
    anchor: date
    steps: list[Step] = field(default_factory=list)
    channels: list[dict] = field(default_factory=list)
    cold_after: date | None = None
    strategy_note: str = ""
    expected_lift: str = ""

    def as_dict(self) -> dict:
        return {
            "stage": self.stage,
            "anchor": self.anchor.isoformat(),
            "steps": [s.as_dict() for s in self.steps],
            "channels": self.channels,
            "cold_after": self.cold_after.isoformat() if self.cold_after else None,
            "cold_after_human": self.cold_after.strftime("%a %d %b %Y") if self.cold_after else "",
            "strategy_note": self.strategy_note,
            "expected_lift": self.expected_lift,
        }


def _first_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return "there"
    return n.replace("Mr.", "").replace("Ms.", "").replace("Dr.", "").strip().split()[0]


def build_plan(
    *,
    stage: str,
    anchor: date | None = None,
    candidate_name: str = "",
    recruiter_name: str = "",
    role: str = "",
    company: str = "",
    hook: str = "",
    stated_timeline: str = "",
) -> FollowUpPlan:
    """
    stage: applied | phone_screen | interview | offer_pending
    anchor: the date the stage happened (defaults to today)
    hook: one specific thing that makes you the memorable candidate
    """
    anchor = anchor or date.today()
    role = (role or "the role").strip()
    company = (company or "your team").strip()
    you = (candidate_name or "").strip() or "me"
    them = _first_name(recruiter_name)
    hook = (hook or "").strip()

    steps: list[Step] = []
    cold: date | None = None
    note = ""
    lift = ("Following up within 1-2 weeks correlates with roughly a 20% lift in "
            "callback rates (Resume Worded, n=1,200). 57% of candidates never do it.")

    if stage == "applied":
        note = (
            "The recruiter shortlists in the week after your application lands. Your "
            "follow-up is timed to arrive inside that window, not after it closes. "
            "Send one, then one more, then stop - three touches maximum."
        )
        # Default: 6 business days, the midpoint of the 5-7 day window that works.
        d1 = add_business_days(anchor, 6)

        # If the recruiter gave you a timeline, chasing before it expires reads as
        # impatience. Defer to two business days past the date they named.
        tl_days = _parse_timeline_days(stated_timeline)
        if stated_timeline:
            if tl_days is not None:
                tl_end = anchor + timedelta(days=tl_days)
                d1 = add_business_days(tl_end, 2)
                note = (
                    f"They gave you a timeline of \"{stated_timeline}\" - about "
                    f"{tl_days} calendar days, ending "
                    f"{tl_end.strftime('%d %B')}. Your first chase only becomes "
                    f"legitimate once that date has passed, so it is scheduled two "
                    f"business days after it."
                )
            else:
                d1 = add_business_days(anchor, 10)
                note = (
                    f"They gave you a timeline of \"{stated_timeline}\", which I could "
                    f"not parse into a date. I have pushed the first chase out to 10 "
                    f"business days rather than risk chasing inside the window they "
                    f"asked you to respect."
                )

        # Later touches keep their original 7- and 8-day spacing from the first,
        # so a deferred schedule does not stack touches on top of each other.
        d2 = add_business_days(d1, 7)
        cold = add_business_days(d2, 8)

        steps.append(Step(
            label="Follow-up 1 - confirm receipt, add one piece of evidence",
            day=d1, offset_business_days=business_days_between(anchor, d1),
            subject=f"Application for {role} - {you}",
            body=(
                f"Dear {them},\n\n"
                f"I applied for the {role} position at {company} on "
                f"{anchor.strftime('%d %B')} and wanted to confirm my application "
                f"reached you.\n\n"
                + (f"{hook}\n\n" if hook else "")
                + f"I remain very interested in the role and would welcome the chance "
                f"to discuss how my background fits what {company} is building. I am "
                f"happy to provide references, a portfolio, or a short sample of "
                f"relevant work if that would help.\n\n"
                f"Thank you for your time and consideration.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email to the recruiter or hiring manager",
            rationale="5-7 business days after an online application when no timeline "
                      "was given. Adding one new piece of evidence gives them a reason "
                      "to reopen the file rather than just re-reading it.",
        ))

        steps.append(Step(
            label="Follow-up 2 - short, specific, no guilt",
            day=d2, offset_business_days=business_days_between(anchor, d2),
            subject=f"Re: Application for {role} - {you}",
            body=(
                f"Dear {them},\n\n"
                f"A brief follow-up on my application for the {role} role. I know "
                f"hiring cycles move at their own pace, so please take this as a note "
                f"of continued interest rather than a request for an update.\n\n"
                f"If the role has been filled or the search is on hold, a one-line "
                f"reply would be genuinely appreciated - it lets me close the loop "
                f"cleanly.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email, or LinkedIn if email has bounced",
            rationale="Day 13. Explicitly offering an easy 'no' materially raises reply "
                      "rates, because the recruiter no longer has to compose a rejection.",
        ))

        steps.append(Step(
            label="Graceful close - then stop chasing",
            day=cold, offset_business_days=business_days_between(anchor, cold),
            subject=f"Closing my application for {role}",
            body=(
                f"Dear {them},\n\n"
                f"I have not heard back on the {role} position, so I will assume the "
                f"search has moved on and close my application on my side.\n\n"
                f"Thank you for considering it. If a similar role opens in future, I "
                f"would be glad to be thought of.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email",
            rationale="14-21 days of silence means the trail has gone cold. Closing "
                      "gracefully costs nothing and occasionally reopens the "
                      "conversation; it also lets you stop spending emotional energy "
                      "on a dead requisition.",
        ))

    elif stage == "phone_screen":
        note = ("Phone screens convert or die fast. The hiring manager is usually "
                "deciding within days, so a 3-5 business day window is the sweet spot.")
        d1 = add_business_days(anchor, 4)
        steps.append(Step(
            label="Post-screen follow-up - restate the fit",
            day=d1, offset_business_days=4,
            subject=f"Thank you - {role} screening call",
            body=(
                f"Dear {them},\n\n"
                f"Thank you for the screening call on {anchor.strftime('%d %B')}. "
                f"It sharpened my interest in the {role} role considerably.\n\n"
                + (f"{hook}\n\n" if hook else
                   "You mentioned the priorities for the first six months. Based on "
                   "what you described, I am confident I could contribute from week "
                   "one.\n\n")
                + f"Please let me know if there is anything further you need from me "
                f"before the next stage.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email to whoever conducted the screen",
            rationale="3-5 business days after a phone screen is the accepted window.",
        ))
        d2 = add_business_days(anchor, 10)
        steps.append(Step(
            label="Second check-in",
            day=d2, offset_business_days=10,
            subject=f"Re: {role} - next steps",
            body=(
                f"Dear {them},\n\n"
                f"Checking in on the {role} process. I remain keen and am available at "
                f"short notice for the next stage.\n\n"
                f"If the timeline has shifted, no problem at all - just let me know "
                f"roughly when to expect an update.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email",
            rationale="Day 10. Asking for a timeline rather than a decision is easier "
                      "to answer and gets a reply more often.",
        ))
        cold = add_business_days(anchor, 18)

    elif stage == "interview":
        note = ("Two distinct moves here: a thank-you inside 48 hours, which is "
                "table stakes, and a substantive follow-up at 1-2 weeks.")
        d0 = add_business_days(anchor, 1)
        steps.append(Step(
            label="Thank-you note - within 24-48 hours, non-negotiable",
            day=d0, offset_business_days=1,
            subject=f"Thank you - {role} interview",
            body=(
                f"Dear {them},\n\n"
                f"Thank you for the time yesterday discussing the {role} role. I "
                f"particularly enjoyed the part of the conversation about "
                f"{hook or 'the direction the team is heading'}.\n\n"
                f"It reinforced my belief that I could add real value, and I would "
                f"welcome the opportunity to do so.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email, same day or next morning",
            rationale="24-48 hours after an interview. Referencing one specific thing "
                      "from the conversation is what separates this from a template.",
        ))
        d1 = add_business_days(anchor, 9)
        steps.append(Step(
            label="Substantive follow-up with new evidence",
            day=d1, offset_business_days=9,
            subject=f"Re: {role} - a thought following our conversation",
            body=(
                f"Dear {them},\n\n"
                f"Since our conversation about the {role} role I have been thinking "
                f"about {hook or 'the challenge you described'}, and I wanted to share "
                f"a brief thought on how I would approach it.\n\n"
                f"I remain very interested and would be glad to discuss further at any "
                f"stage.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email",
            rationale="1-2 weeks after the interview. Bringing something new is the "
                      "only follow-up that reliably earns a reply at this stage.",
        ))
        cold = add_business_days(anchor, 21)

    elif stage == "offer_pending":
        note = "Offers stall for boring reasons - budget sign-off, a competing " \
               "candidate, a leave of absence. A calm nudge is appropriate and rarely " \
               "costs you the offer."
        d1 = add_business_days(anchor, 5)
        steps.append(Step(
            label="Nudge on the outstanding offer",
            day=d1, offset_business_days=5,
            subject=f"{role} - following up on the offer",
            body=(
                f"Dear {them},\n\n"
                f"I wanted to follow up on the {role} offer and confirm that my "
                f"enthusiasm for joining {company} is unchanged.\n\n"
                f"Please let me know if any further documentation or clarification is "
                f"needed from my side, and roughly when I might expect the formal "
                f"confirmation.\n\n"
                f"Kind regards,\n{you}"
            ),
            channel="Direct email, copied to HR if separate",
            rationale="5 business days. Confirming continued interest removes the main "
                      "reason offers stall: fear that you have taken something else.",
        ))
        cold = add_business_days(anchor, 14)
    else:
        note = "Unknown stage - defaulting to the application schedule."
        return build_plan(stage="applied", anchor=anchor, candidate_name=candidate_name,
                          recruiter_name=recruiter_name, role=role, company=company,
                          hook=hook, stated_timeline=stated_timeline)

    return FollowUpPlan(
        stage=stage, anchor=anchor, steps=steps, channels=CHANNELS,
        cold_after=cold, strategy_note=note, expected_lift=lift,
    )
