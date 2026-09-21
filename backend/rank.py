"""Ranking algorithm — match candidates to a job description.

The match score blends three interpretable signals:

  1. **Skill coverage** — the share of the job's required skills the candidate has.
  2. **Text similarity** — TF-IDF cosine similarity between the resume and the JD.
  3. **Experience fit** — how well the candidate's years meet the required minimum.

The weights live in ``config.py`` and are chosen so the score is dominated by
concrete skill coverage while still rewarding overall relevance and seniority.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config
from .extract import Candidate, extract_skills
from data.skills import canonical

# Requirements phrased as "3+ years", "minimum 5 years", etc.
import re

_MIN_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs)", re.I)


@dataclass
class JobPosting:
    raw_text: str
    required_skills: list[str] = field(default_factory=list)
    min_years: int = 0

    def as_dict(self) -> dict:
        return {"required_skills": self.required_skills, "min_years": self.min_years}


@dataclass
class ScoreBreakdown:
    candidate: Candidate
    total: float
    skill_coverage: float
    similarity: float
    experience_fit: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "candidate": self.candidate.as_dict(),
            "score": round(self.total, 4),
            "is_match": self.total >= config.MATCH_THRESHOLD,
            "breakdown": {
                "skill_coverage": round(self.skill_coverage, 4),
                "similarity": round(self.similarity, 4),
                "experience_fit": round(self.experience_fit, 4),
            },
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
        }


def parse_job(text: str) -> JobPosting:
    """Extract required skills and minimum years from a job description."""
    skills = extract_skills(text)
    years = [int(m.group(1)) for m in _MIN_YEARS.finditer(text)]
    return JobPosting(raw_text=text, required_skills=skills, min_years=max(years) if years else 0)


def _experience_fit(candidate_years: float, min_years: int) -> float:
    if min_years <= 0:
        return 1.0
    return min(1.0, candidate_years / min_years)


def rank(job: JobPosting, candidates: list[Candidate]) -> list[ScoreBreakdown]:
    """Score and rank candidates against a job posting (best first)."""
    if not candidates:
        return []

    # Shared TF-IDF space over the JD + all resumes so IDF is comparable.
    corpus = [job.raw_text] + [c.raw_text for c in candidates]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    required = {canonical(s) for s in job.required_skills}
    results: list[ScoreBreakdown] = []

    for candidate, sim in zip(candidates, sims):
        cand_skills = {canonical(s) for s in candidate.skills}
        matched = sorted(required & cand_skills)
        missing = sorted(required - cand_skills)
        coverage = len(matched) / len(required) if required else float(sim)
        exp_fit = _experience_fit(candidate.years_experience, job.min_years)

        total = (
            config.WEIGHT_SKILLS * coverage
            + config.WEIGHT_SIMILARITY * float(sim)
            + config.WEIGHT_EXPERIENCE * exp_fit
        )
        results.append(ScoreBreakdown(
            candidate=candidate,
            total=total,
            skill_coverage=coverage,
            similarity=float(sim),
            experience_fit=exp_fit,
            matched_skills=matched,
            missing_skills=missing,
        ))

    results.sort(key=lambda r: r.total, reverse=True)
    return results


def score_one(job_text: str, resume_text: str, name: str | None = None) -> ScoreBreakdown:
    """Convenience: parse a JD + a single resume and return the score."""
    from .extract import extract_resume

    job = parse_job(job_text)
    candidate = extract_resume(resume_text, name=name)
    return rank(job, [candidate])[0]
