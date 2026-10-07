"""
SHORTLIST API.

Four engines, one workflow:
  1. /api/ghost    - is this job even real? (run this FIRST)
  2. /api/match    - where do you rank, and what search string finds you?
  3. /api/bullets  - turn duties into evidence
  4. /api/followup - run the chase schedule that lifts callbacks ~20%

Static frontend served from /static.
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import ats_match, bullets, followup, ghost_radar
from .models import (BulletRequest, FollowUpRequest, GhostRequest, MatchRequest,
                     PipelineAdd, PipelineMove)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_FILE = Path(os.environ.get("SHORTLIST_DATA", BASE_DIR / "pipeline.json"))

_pipeline: dict[str, dict] = {}


def _load_pipeline() -> None:
    global _pipeline
    if DATA_FILE.exists():
        try:
            _pipeline = json.loads(DATA_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            _pipeline = {}


def _save_pipeline() -> None:
    DATA_FILE.write_text(json.dumps(_pipeline, indent=2))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_pipeline()
    yield


app = FastAPI(
    title="SHORTLIST",
    version="1.0.0",
    description="Know if the job is real. Then get on the shortlist.",
    lifespan=lifespan,
)


# --------------------------------------------------------------------------
# Engines
# --------------------------------------------------------------------------

@app.post("/api/ghost")
def ghost(req: GhostRequest):
    """Score a posting or recruiter message for ghost-job and scam risk."""
    if not any([req.job_description.strip(), req.contact_text.strip(),
                req.company_name.strip(), req.job_title.strip()]):
        raise HTTPException(400, "Give me something to analyse: a job description, "
                                  "the recruiter's message, or at least a company name.")
    report = ghost_radar.analyze(
        job_title=req.job_title,
        company_name=req.company_name,
        job_description=req.job_description,
        contact_text=req.contact_text,
        contact_email=req.contact_email,
        contact_channel=req.contact_channel,
        company_website=req.company_website,
        listing_age_days=req.listing_age_days,
        reposted=req.reposted,
        salary_listed=req.salary_listed,
        payment_requested=req.payment_requested,
        payment_to=req.payment_to,
        interview_mode=req.interview_mode,
        unsolicited=req.unsolicited,
        applicant_count=req.applicant_count,
    )
    return report.as_dict()


@app.post("/api/match")
def match(req: MatchRequest):
    """Score resume alignment, estimate rank, build the recruiter's search string."""
    if not req.job_description.strip():
        raise HTTPException(400, "A job description is required.")
    if not req.resume.strip():
        raise HTTPException(400, "Your resume text is required.")
    if req.reviewed >= req.pool_size:
        raise HTTPException(400, "The number reviewed cannot exceed the pool size.")
    report = ats_match.analyze(req.job_description, req.resume,
                               pool_size=req.pool_size, reviewed=req.reviewed)
    return report.as_dict()


@app.post("/api/bullets")
def bullet_lab(req: BulletRequest):
    """Diagnose weak bullets and build evidence scaffolds."""
    items = [b for b in req.bullets if b.strip()]
    if not items and req.resume.strip():
        fixes = bullets.fix_resume_bullets(req.resume)
        return {"fixes": [f.as_dict() for f in fixes], "source": "resume"}
    if not items:
        raise HTTPException(400, "Send at least one bullet, or paste your resume.")
    return {"fixes": [bullets.fix_bullet(b).as_dict() for b in items], "source": "bullets"}


@app.post("/api/followup")
def follow_up(req: FollowUpRequest):
    """Build a dated chase schedule and write the emails."""
    anchor = req.anchor or date.today()
    plan = followup.build_plan(
        stage=req.stage, anchor=anchor, candidate_name=req.candidate_name,
        recruiter_name=req.recruiter_name, role=req.role, company=req.company,
        hook=req.hook, stated_timeline=req.stated_timeline,
    )
    return plan.as_dict()


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

@app.get("/api/pipeline")
def pipeline_list():
    apps = sorted(_pipeline.values(), key=lambda a: a.get("added_at", ""), reverse=True)
    stages = ["found", "vetted", "applied", "following_up", "interview", "offer", "rejected"]
    counts = {s: sum(1 for a in apps if a.get("stage") == s) for s in stages}
    blocked = sum(1 for a in apps if a.get("ghost_verdict") in {"DANGER", "HIGH RISK"})
    return {
        "applications": apps,
        "counts": counts,
        "blocked_by_ghost_radar": blocked,
        "naira_protected": sum(a.get("naira_at_risk", 0) for a in apps
                               if a.get("ghost_verdict") in {"DANGER", "HIGH RISK"}),
    }


@app.post("/api/pipeline")
def pipeline_add(req: PipelineAdd):
    app_id = uuid.uuid4().hex[:12]
    rec = req.application.model_dump()
    rec["id"] = app_id
    rec["added_at"] = date.today().isoformat()
    _pipeline[app_id] = rec
    _save_pipeline()
    return rec


@app.patch("/api/pipeline/{app_id}")
def pipeline_move(app_id: str, req: PipelineMove):
    if app_id not in _pipeline:
        raise HTTPException(404, f"No application with id {app_id}")
    _pipeline[app_id]["stage"] = req.stage
    _save_pipeline()
    return _pipeline[app_id]


@app.delete("/api/pipeline/{app_id}")
def pipeline_delete(app_id: str):
    if app_id not in _pipeline:
        raise HTTPException(404, f"No application with id {app_id}")
    del _pipeline[app_id]
    _save_pipeline()
    return {"deleted": app_id}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0", "applications_tracked": len(_pipeline)}


# --------------------------------------------------------------------------
# Static
# --------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
