"""FastAPI backend for the resume screener.

Endpoints:
    GET  /health         liveness check
    POST /extract        parse one resume -> structured profile
    POST /score          score one resume against a job description
    POST /rank           rank many resumes against a job description

Run:
    uvicorn backend.api:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .extract import extract_resume
from .rank import parse_job, rank

app = FastAPI(
    title="AI-Powered Resume Screener",
    version="0.1.0",
    description="NLP extraction + candidate-to-job ranking.",
)

# Allow the React dev server (and any local origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResumeIn(BaseModel):
    text: str = Field(..., description="Raw resume text")
    name: str | None = None


class ScoreIn(BaseModel):
    job_description: str
    resume: str
    name: str | None = None


class Candidate(BaseModel):
    name: str | None = None
    text: str


class RankIn(BaseModel):
    job_description: str
    candidates: list[Candidate]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract")
def extract(body: ResumeIn) -> dict:
    return extract_resume(body.text, name=body.name).as_dict()


@app.post("/score")
def score(body: ScoreIn) -> dict:
    job = parse_job(body.job_description)
    candidate = extract_resume(body.resume, name=body.name)
    result = rank(job, [candidate])[0]
    return {"job": job.as_dict(), **result.as_dict()}


@app.post("/rank")
def rank_candidates(body: RankIn) -> dict:
    job = parse_job(body.job_description)
    candidates = [extract_resume(c.text, name=c.name) for c in body.candidates]
    ranked = rank(job, candidates)
    return {
        "job": job.as_dict(),
        "results": [r.as_dict() for r in ranked],
    }
