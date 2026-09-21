"""Synthetic, labeled (job, resume) pairs for evaluating the ranker.

The label models a realistic hiring decision rather than a clean role split, so
the benchmark reflects how the screener would perform on genuinely ambiguous
candidates instead of trivially separable ones:

  * A candidate is a **true match (label 1)** when they cover at least
    ``COVERAGE_BAR`` of the required skills *and* meet the minimum years —
    the rule a human recruiter would roughly apply.
  * Candidates span the full spectrum from clearly under-qualified to clearly
    over-qualified, including **borderline** cases near the bar.
  * **Hard negatives** come from adjacent roles that share a skill or two.
  * ``LABEL_NOISE`` of labels are flipped to model human inconsistency.

The ranker never sees these labels; it approximates the decision from its own
blended score, so agreement is high but realistically imperfect.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

# role -> (core skills, plausible titles, adjacent filler skills)
ROLES: dict[str, dict] = {
    "backend": {
        "title": "Backend Engineer",
        "skills": ["python", "fastapi", "postgresql", "docker", "rest api", "redis", "microservices"],
        "filler": ["git", "linux", "agile", "unit testing"],
    },
    "frontend": {
        "title": "Frontend Engineer",
        "skills": ["react", "javascript", "typescript", "css", "redux", "html", "next.js"],
        "filler": ["git", "webpack", "agile", "code review"],
    },
    "ml": {
        "title": "Machine Learning Engineer",
        "skills": ["python", "pytorch", "machine learning", "nlp", "pandas", "numpy", "scikit-learn"],
        "filler": ["git", "docker", "aws", "sql"],
    },
    "data": {
        "title": "Data Engineer",
        "skills": ["spark", "airflow", "sql", "etl", "aws", "python", "kafka"],
        "filler": ["git", "docker", "linux", "data engineering"],
    },
    "devops": {
        "title": "DevOps Engineer",
        "skills": ["kubernetes", "docker", "terraform", "aws", "ci/cd", "linux", "jenkins"],
        "filler": ["git", "bash", "prometheus", "grafana"],
    },
}

# Ground-truth "hiring rule" the labels follow.
COVERAGE_BAR = 0.60   # must cover >= 60% of required skills
LABEL_NOISE = 0.10    # fraction of labels flipped (human inconsistency)

_FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Drew", "Cameron"]
_LAST = ["Lee", "Patel", "Garcia", "Nguyen", "Smith", "Kim", "Brown", "Silva", "Khan", "Rossi"]
_COMPANIES = ["Northwind", "Acme Corp", "Globex", "Initech", "Umbrella", "Hooli", "Stark Labs"]
_FIELDS = ["Computer Science", "Software Engineering", "Data Science", "Information Systems"]
_DEGREES = ["Bachelor's", "Master's"]


@dataclass
class LabeledPair:
    job_text: str
    resume_text: str
    label: int  # 1 = good match, 0 = not a match
    role: str


def _job_text(rng: random.Random, role_key: str, min_years: int) -> str:
    role = ROLES[role_key]
    skills = role["skills"]
    return (
        f"Job Title: {role['title']}\n"
        f"We are hiring a {role['title']} to join our growing engineering team. "
        f"This role requires {min_years}+ years of professional experience.\n\n"
        "Requirements:\n"
        + "\n".join(f"- Strong hands-on experience with {s}" for s in skills)
        + "\n- Collaborate across teams to ship reliable, well-tested software."
    )


def _resume_text(rng: random.Random, role_key: str, years: int, skills: list[str]) -> str:
    role = ROLES[role_key]
    name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
    title = role["title"]
    company = rng.choice(_COMPANIES)
    start = 2024 - years
    bullets = [
        f"- Built and maintained production systems using {skills[i % len(skills)]}."
        for i in range(min(3, max(1, len(skills))))
    ]
    return (
        f"{name}\n"
        f"{title} with {years}+ years of experience.\n\n"
        f"Skills: {', '.join(skills)}\n\n"
        "Experience:\n"
        f"{title} at {company} ({start} - Present)\n"
        + "\n".join(bullets)
        + "\n\nEducation:\n"
        f"{rng.choice(_DEGREES)} in {rng.choice(_FIELDS)}"
    )


def _sample_subset(rng: random.Random, items: list[str], keep_frac: float) -> list[str]:
    k = max(1, round(len(items) * keep_frac))
    return rng.sample(items, min(k, len(items)))


def _label(required: list[str], candidate_skills: list[str], years: int, min_years: int,
           rng: random.Random) -> int:
    """Apply the ground-truth hiring rule, then inject a little label noise."""
    req = set(required)
    coverage = len(req & set(candidate_skills)) / len(req) if req else 0.0
    label = 1 if (coverage >= COVERAGE_BAR and years >= min_years) else 0
    if rng.random() < LABEL_NOISE:
        label = 1 - label
    return label


def generate_pair(rng: random.Random) -> LabeledPair:
    role_key = rng.choice(list(ROLES))
    role = ROLES[role_key]
    required = role["skills"]
    min_years = rng.choice([2, 3, 4, 5])
    job = _job_text(rng, role_key, min_years)

    # 65% same-role candidates spanning under- to over-qualified; 35% adjacent
    # role candidates (mostly negatives, some hard negatives sharing skills).
    if rng.random() < 0.65:
        # Coverage anywhere from weak (0.2) to full (1.0) — borderline included.
        kept = _sample_subset(rng, required, keep_frac=rng.uniform(0.2, 1.0))
        kept += _sample_subset(rng, role["filler"], keep_frac=rng.uniform(0.0, 0.6))
        years = max(1, min_years + rng.choice([-3, -2, -1, 0, 0, 1, 2, 3]))
        src_role = role_key
    else:
        other_key = rng.choice([k for k in ROLES if k != role_key])
        kept = _sample_subset(rng, ROLES[other_key]["skills"], keep_frac=rng.uniform(0.5, 1.0))
        kept += _sample_subset(rng, ROLES[other_key]["filler"], keep_frac=0.4)
        # Hard negative: sometimes carry over 1-3 of the target's skills.
        if rng.random() < 0.5:
            kept += _sample_subset(rng, required, keep_frac=rng.uniform(0.1, 0.4))
        years = rng.choice([1, 2, 3, 4, 5, 6])
        src_role = other_key

    kept = sorted(set(kept))
    label = _label(required, kept, years, min_years, rng)
    resume = _resume_text(rng, src_role, years, kept)
    return LabeledPair(job, resume, label, role_key)


def generate_dataset(n: int = 600, seed: int = 42) -> list[LabeledPair]:
    """Generate ``n`` labeled (job, resume) pairs with realistic ambiguity."""
    rng = random.Random(seed)
    pairs = [generate_pair(rng) for _ in range(n)]
    rng.shuffle(pairs)
    return pairs
