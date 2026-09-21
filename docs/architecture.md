# Architecture

```
                         ┌─────────────────────────────┐
   Job description  ───▶ │  rank.parse_job()           │  required skills, min years
                         └──────────────┬──────────────┘
                                        │
   Resume text  ─────────────────────┐  │
        │                            ▼  ▼
        │                 ┌──────────────────────────┐
        └───────────────▶ │  extract.extract_resume()│  NLP pipeline
                          │  • skills (gazetteer)    │  → Candidate profile
                          │  • years of experience   │
                          │  • education (degree)    │
                          └────────────┬─────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │  rank.rank()             │
                          │  0.60·skill coverage     │  → score ∈ [0,1]
                          │  0.25·TF-IDF similarity  │     + matched/missing skills
                          │  0.15·experience fit     │
                          └────────────┬─────────────┘
                                       │
                 ┌─────────────────────┼──────────────────────┐
                 ▼                     ▼                       ▼
        FastAPI /rank        backend.evaluate            React dashboard
        (backend/api.py)     (accuracy benchmark)        (frontend/)
```

## Components

**NLP extraction (`backend/extract.py`).** Deliberately dependency-light — a
curated skills gazetteer (`data/skills.py`) plus regular expressions rather than
a heavyweight model. Skills are canonicalized (`sklearn` → `scikit-learn`,
`nodejs` → `node.js`) so a resume and a JD phrased differently still match.
Experience is read from explicit statements ("5+ years") or summed from dated
employment ranges; education is detected by degree keywords.

**Ranking (`backend/rank.py`).** A transparent weighted blend of three signals:
skill coverage (how much of the JD's required skills the candidate has), TF-IDF
cosine similarity between the resume and JD, and experience fit against the
minimum years. Every score ships with the matched and missing skills, so a
recruiter can see *why* a candidate ranked where they did.

**Evaluation (`backend/evaluate.py`, `backend/dataset.py`).** A synthetic but
realistic labeled benchmark: candidates span under- to over-qualified, hard
negatives share skills with the target role, and ~10% label noise models human
inconsistency. The decision threshold is tuned on a train split and metrics are
reported on a held-out test split, so the headline accuracy isn't inflated by
tuning on the same data it's measured on.

**API (`backend/api.py`).** FastAPI with CORS, exposing `/extract`, `/score`,
and `/rank`.

**Dashboard (`frontend/`).** A Vite + React single page: paste a job
description, add candidate resumes, and get an interactive ranked list with
score bars, matched/missing skill chips, and each candidate's experience and
education. In dev it proxies `/api` to the backend on port 8000.
