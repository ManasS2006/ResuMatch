"""A curated gazetteer of skills the extractor recognizes.

Grouped only for readability; the extractor flattens them. Multi-word skills are
supported (matched with word boundaries, case-insensitive).
"""
from __future__ import annotations

SKILL_GROUPS: dict[str, list[str]] = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "dart", "sql", "bash", "shell",
    ],
    "ml_ai": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision", "reinforcement learning",
        "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras", "xgboost",
        "gradient boosting", "random forest", "transformers", "hugging face",
        "spacy", "nltk", "opencv", "pandas", "numpy", "llm",
        "large language models", "prompt engineering", "rag",
    ],
    "web_backend": [
        "fastapi", "flask", "django", "node.js", "nodejs", "express",
        "spring", "spring boot", "rest", "rest api", "graphql", "grpc",
        "microservices", "redis", "rabbitmq", "kafka",
    ],
    "web_frontend": [
        "react", "react.js", "next.js", "vue", "angular", "svelte",
        "html", "css", "tailwind", "redux", "vite", "webpack",
    ],
    "data": [
        "postgresql", "mysql", "mongodb", "sqlite", "elasticsearch",
        "snowflake", "spark", "hadoop", "airflow", "dbt", "etl",
        "data engineering", "data analysis", "tableau", "power bi",
    ],
    "devops_cloud": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "terraform", "ci/cd", "jenkins", "github actions", "linux", "git",
        "ansible", "prometheus", "grafana",
    ],
    "practices": [
        "agile", "scrum", "unit testing", "tdd", "code review",
        "system design", "distributed systems", "object-oriented programming",
    ],
}

# Flat, de-duplicated list of all known skills.
ALL_SKILLS: list[str] = sorted(
    {skill for group in SKILL_GROUPS.values() for skill in group}
)

# Canonicalization: map synonyms/variants to a single display form so a resume
# saying "sklearn" and a JD saying "scikit-learn" count as the same skill.
CANONICAL: dict[str, str] = {
    "sklearn": "scikit-learn",
    "golang": "go",
    "nodejs": "node.js",
    "react.js": "react",
    "natural language processing": "nlp",
    "large language models": "llm",
    "google cloud": "gcp",
}


def canonical(skill: str) -> str:
    """Return the canonical form of a skill token."""
    s = skill.strip().lower()
    return CANONICAL.get(s, s)
