"""Request/response schemas."""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GhostRequest(BaseModel):
    job_title: str = ""
    company_name: str = ""
    job_description: str = ""
    contact_text: str = Field(default="", description="Paste the recruiter's message here")
    contact_email: str = ""
    contact_channel: str = ""
    company_website: str = ""
    listing_age_days: Optional[int] = None
    reposted: bool = False
    salary_listed: Optional[bool] = None
    payment_requested: Optional[bool] = None
    payment_to: str = "none"
    interview_mode: str = ""
    unsolicited: bool = False
    applicant_count: Optional[int] = None


class MatchRequest(BaseModel):
    job_description: str
    resume: str
    pool_size: int = Field(default=180, ge=5, le=100000)
    reviewed: int = Field(default=20, ge=1, le=10000)


class BulletRequest(BaseModel):
    bullets: list[str] = Field(default_factory=list)
    resume: str = ""


class FollowUpRequest(BaseModel):
    stage: Literal["applied", "phone_screen", "interview", "offer_pending"] = "applied"
    anchor: Optional[date] = None
    candidate_name: str = ""
    recruiter_name: str = ""
    role: str = ""
    company: str = ""
    hook: str = ""
    stated_timeline: str = ""


class ApplicationIn(BaseModel):
    company: str
    role: str
    stage: str = "found"
    ghost_score: int = 0
    ghost_verdict: str = ""
    match_rate: int = 0
    source: str = ""
    applied_on: Optional[date] = None
    notes: str = ""


class PipelineAdd(BaseModel):
    application: ApplicationIn


class PipelineMove(BaseModel):
    app_id: str
    stage: str
