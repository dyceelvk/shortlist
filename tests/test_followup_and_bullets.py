"""Tests for the follow-up scheduler and the bullet lab."""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import bullets, followup  # noqa: E402


# ---------------------------- follow-up -----------------------------------

def test_business_days_skip_weekends():
    # Friday 2026-10-02 + 1 business day = Monday 2026-10-05
    assert followup.add_business_days(date(2026, 10, 2), 1) == date(2026, 10, 5)
    # Friday + 5 business days = the following Friday
    assert followup.add_business_days(date(2026, 10, 2), 5) == date(2026, 10, 9)
    # zero offset is a no-op
    assert followup.add_business_days(date(2026, 10, 2), 0) == date(2026, 10, 2)


def test_applied_schedule_has_three_touches_in_order():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                               candidate_name="Ada Obi", recruiter_name="Mr. Bello",
                               role="Data Analyst", company="GTBank")
    assert len(plan.steps) == 3
    days = [s.day for s in plan.steps]
    assert days == sorted(days), days
    assert all(d.weekday() < 5 for d in days), "no step may land on a weekend"
    assert plan.steps[0].offset_business_days == 6
    assert plan.cold_after == days[-1]


def test_first_follow_up_lands_in_the_5_to_7_business_day_window():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1))
    off = plan.steps[0].offset_business_days
    assert 5 <= off <= 7, off


def test_emails_are_personalised():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                               candidate_name="Ada Obi", recruiter_name="Dr. Ngozi Bello",
                               role="Data Analyst", company="GTBank",
                               hook="I cut reporting turnaround by 40% at my last role.")
    first = plan.steps[0]
    assert "Ada Obi" in first.body
    assert "Ngozi" in first.body           # first name only, title stripped
    assert "Data Analyst" in first.body
    assert "GTBank" in first.body
    assert "40%" in first.body
    assert first.subject


def test_business_days_between_counts_correctly():
    assert followup.business_days_between(date(2026, 10, 1), date(2026, 10, 1)) == 0
    assert followup.business_days_between(date(2026, 10, 2), date(2026, 10, 5)) == 1
    assert followup.business_days_between(date(2026, 10, 2), date(2026, 10, 9)) == 5
    assert followup.business_days_between(date(2026, 10, 9), date(2026, 10, 2)) == -5
    # round-trip: add then measure
    for n in range(0, 25):
        a = date(2026, 3, 4)
        assert followup.business_days_between(a, followup.add_business_days(a, n)) == n


@pytest.mark.parametrize("text,expected", [
    ("three weeks", 21), ("2 weeks", 14), ("10 days", 10), ("one month", 30),
    ("a fortnight", 14), ("two months", 60), ("", None), ("soon", None),
    ("end of the month", None),
])
def test_timeline_parsing(text, expected):
    assert followup._parse_timeline_days(text) == expected


def test_reported_offset_always_matches_the_actual_date():
    """The bug that broke: offset_business_days used to be hardcoded to 6 while
    the date was computed separately, so the two disagreed."""
    for tl in ["", "three weeks", "2 weeks", "10 days", "soon", "a month"]:
        plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                                   stated_timeline=tl)
        for s in plan.steps:
            assert s.offset_business_days == followup.business_days_between(
                plan.anchor, s.day), (tl, s.label, s.offset_business_days, s.day)


def test_stated_timeline_defers_the_first_chase():
    """Chasing inside a window the recruiter asked you to respect reads as
    impatience, so a stated timeline must push the first touch LATER."""
    normal = followup.build_plan(stage="applied", anchor=date(2026, 10, 1))
    deferred = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                                   stated_timeline="three weeks")
    assert deferred.steps[0].offset_business_days > normal.steps[0].offset_business_days
    # "three weeks" from 1 Oct ends 22 Oct; two business days later is 26 Oct.
    assert deferred.steps[0].day == date(2026, 10, 26), deferred.steps[0].day
    assert "timeline" in deferred.strategy_note.lower()


def test_unparseable_timeline_still_defers_rather_than_chasing_early():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                               stated_timeline="sometime next quarter")
    assert plan.steps[0].offset_business_days >= 10
    assert "could not parse" in plan.strategy_note


def test_deferred_schedule_keeps_touches_ordered_and_spaced():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1),
                               stated_timeline="three weeks")
    days = [s.day for s in plan.steps]
    assert days == sorted(set(days)), days
    assert plan.cold_after == days[-1]
    assert all(d.weekday() < 5 for d in days)


def test_interview_thank_you_within_two_business_days():
    plan = followup.build_plan(stage="interview", anchor=date(2026, 10, 1))
    assert plan.steps[0].offset_business_days <= 2
    assert "thank" in plan.steps[0].label.lower()


def test_phone_screen_window_is_tighter_than_application():
    screen = followup.build_plan(stage="phone_screen", anchor=date(2026, 10, 1))
    applied = followup.build_plan(stage="applied", anchor=date(2026, 10, 1))
    assert 3 <= screen.steps[0].offset_business_days <= 5
    assert screen.steps[0].offset_business_days < applied.steps[0].offset_business_days


def test_offer_pending_plan():
    plan = followup.build_plan(stage="offer_pending", anchor=date(2026, 10, 1),
                               company="Flutterwave")
    assert plan.steps
    assert plan.steps[0].offset_business_days == 5
    assert "Flutterwave" in plan.steps[0].body


def test_channel_ranking_puts_email_first_and_portal_last_but_one():
    assert followup.CHANNELS[0]["channel"].startswith("Direct email")
    portal = next(c for c in followup.CHANNELS if "portal" in c["channel"].lower())
    assert "~0%" in portal["response_rate"]
    assert portal["rank"] == 5


def test_expected_lift_cites_the_study():
    plan = followup.build_plan(stage="applied", anchor=date(2026, 10, 1))
    assert "20%" in plan.expected_lift
    assert "57%" in plan.expected_lift


def test_serialisable():
    d = followup.build_plan(stage="applied", anchor=date(2026, 10, 1)).as_dict()
    assert d["anchor"] == "2026-10-01"
    assert all("date" in s and "body" in s for s in d["steps"])
    assert d["cold_after_human"]


# ------------------------------ bullet lab --------------------------------

def test_weak_bullet_is_diagnosed():
    fx = bullets.fix_bullet("Responsible for various backend tasks and databases")
    assert fx.problems
    joined = " ".join(fx.problems).lower()
    assert "responsible for" in joined
    assert "no number" in joined
    assert "vague quantifier" in joined
    assert not fx.has_metric
    assert fx.scaffold
    assert fx.verb_options
    assert fx.questions


def test_quantified_bullet_passes():
    fx = bullets.fix_bullet(
        "- Cut settlement errors by 74% across 12,000 merchants by rebuilding "
        "the reconciliation service in Python")
    assert fx.has_metric
    assert not any("no number" in p.lower() for p in fx.problems)


def test_passive_voice_flagged():
    fx = bullets.fix_bullet("The report was prepared and submitted to management weekly")
    assert any("passive" in p.lower() for p in fx.problems)


def test_overlong_bullet_flagged():
    long_bullet = "Built a thing " + "that did stuff " * 12
    fx = bullets.fix_bullet(long_bullet)
    assert any("words" in p.lower() for p in fx.problems)


def test_domain_detection_picks_the_right_verb_bank():
    assert bullets.detect_domain("closed deals and grew revenue in my accounts") == "sales"
    assert bullets.detect_domain("deployed the API to the server and fixed a bug") == "engineering"
    assert bullets.detect_domain("reconciled the ledger and prepared the audit") == "finance"
    assert bullets.detect_domain("managed the team and mentored two juniors") == "leadership"


def test_resume_scan_surfaces_only_broken_bullets():
    resume = """
EXPERIENCE
- Cut settlement errors by 74% across 12,000 merchants by rebuilding reconciliation
- Responsible for handling customer queries
- Assisted with monthly reporting tasks
- Led a team of 5 engineers through an AWS migration, cutting release time by 90%
"""
    fixes = bullets.fix_resume_bullets(resume)
    originals = " ".join(f.original for f in fixes)
    assert "Responsible for handling customer queries" in originals
    assert "Assisted with monthly reporting tasks" in originals
    assert "Cut settlement errors" not in originals


def test_empty_input():
    assert bullets.fix_bullet("").original == ""
    assert bullets.fix_resume_bullets("") == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
