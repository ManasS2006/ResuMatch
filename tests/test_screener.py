"""Tests for extraction, ranking, and evaluation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.extract import extract_resume, extract_skills, extract_years_experience
from backend.rank import parse_job, rank, score_one
from backend.evaluate import evaluate

SAMPLE_RESUME = """
Dana Wells
Machine Learning Engineer with 6+ years of experience.
Skills: Python, PyTorch, machine learning, NLP, pandas, scikit-learn, Docker
Experience:
ML Engineer at Globex (2018 - Present)
- Built NLP models in PyTorch.
Education: Master's in Computer Science
"""

JOB = """
Machine Learning Engineer, 4+ years required.
Requirements: Python, PyTorch, machine learning, NLP, pandas
"""


def test_extract_skills_canonicalizes():
    skills = extract_skills("Experienced in sklearn, NodeJS and NLP.")
    assert "scikit-learn" in skills  # sklearn -> canonical
    assert "node.js" in skills
    assert "nlp" in skills


def test_extract_years():
    assert extract_years_experience("5+ years of experience") == 5.0
    assert extract_years_experience("worked 2018 - 2023") == 5.0


def test_extract_resume_profile():
    c = extract_resume(SAMPLE_RESUME)
    assert c.name == "Dana Wells"
    assert c.years_experience >= 6
    assert c.highest_degree == "Master's"
    assert "pytorch" in c.skills


def test_parse_job():
    job = parse_job(JOB)
    assert job.min_years == 4
    assert "pytorch" in job.required_skills


def test_score_one_strong_fit_is_match():
    result = score_one(JOB, SAMPLE_RESUME, name="Dana")
    assert result.is_match if hasattr(result, "is_match") else result.total >= 0.60
    assert result.total >= 0.60
    assert "pytorch" in result.matched_skills


def test_ranking_orders_better_candidate_first():
    strong = extract_resume(SAMPLE_RESUME)
    weak = extract_resume("Bob\nFrontend Engineer.\nSkills: React, CSS, HTML\n")
    ranked = rank(parse_job(JOB), [weak, strong])
    assert ranked[0].candidate.raw_text == SAMPLE_RESUME  # strong candidate wins


def test_evaluation_accuracy_is_reasonable():
    result = evaluate(n=400, seed=42, verbose=False)
    # Realistic, non-trivial benchmark: comfortably better than chance (0.5),
    # and not a suspicious ~100%.
    assert 0.80 <= result.accuracy <= 0.95
