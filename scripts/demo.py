"""End-to-end demo: rank a few sample candidates against a job description."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.extract import extract_resume  # noqa: E402
from backend.rank import parse_job, rank  # noqa: E402

JOB = """
Job Title: Backend Engineer
We are hiring a Backend Engineer with 3+ years of experience.
Requirements:
- Strong experience with Python, FastAPI, and PostgreSQL
- Experience with Docker and REST APIs
- Familiarity with Redis and microservices
"""

RESUMES = {
    "Ava (strong fit)": """
Ava Chen
Backend Engineer with 5+ years of experience.
Skills: Python, FastAPI, PostgreSQL, Docker, REST API, Redis, microservices, Git
Experience:
Backend Engineer at Globex (2019 - Present)
- Built REST APIs in Python and FastAPI backed by PostgreSQL.
Education: Bachelor's in Computer Science
""",
    "Ben (frontend, weak fit)": """
Ben Ortiz
Frontend Engineer with 4+ years of experience.
Skills: React, JavaScript, TypeScript, CSS, Redux, HTML
Experience:
Frontend Engineer at Hooli (2020 - Present)
- Built dashboards in React and Redux.
Education: Bachelor's in Software Engineering
""",
    "Cara (partial fit)": """
Cara Idris
Software Engineer with 2+ years of experience.
Skills: Python, Docker, REST API, Git, Linux
Experience:
Software Engineer at Initech (2022 - Present)
- Built Python services deployed with Docker.
Education: Bachelor's in Information Systems
""",
}


def main() -> None:
    job = parse_job(JOB)
    print(f"Required skills: {job.required_skills}")
    print(f"Minimum years: {job.min_years}\n")

    candidates = [extract_resume(text, name=name) for name, text in RESUMES.items()]
    for i, r in enumerate(rank(job, candidates), 1):
        print(f"#{i}  {r.candidate.name:28s} score={r.total:.3f}  "
              f"{'MATCH' if r.total >= 0.60 else 'no match'}")
        print(f"     matched: {r.matched_skills}")
        print(f"     missing: {r.missing_skills}")
        print(f"     years={r.candidate.years_experience}  degree={r.candidate.highest_degree}\n")


if __name__ == "__main__":
    main()
