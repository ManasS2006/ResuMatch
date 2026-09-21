"""NLP pipeline — extract skills, experience, and education from resume text.

Deliberately dependency-light: it uses a curated skills gazetteer plus regular
expressions rather than a large language model, so it runs instantly on any
machine (including a no-GPU laptop) and its decisions are fully explainable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import backend  # noqa: F401  (ensures the top-level `data` package is importable)
from data.skills import ALL_SKILLS, canonical

# Pre-compile one regex per skill with word boundaries. Skills containing
# non-word characters (c++, c#, ci/cd, node.js) can't rely on \b, so we escape
# and wrap them with lookarounds that treat surrounding whitespace/punctuation
# as boundaries.
def _skill_pattern(skill: str) -> re.Pattern[str]:
    # Boundaries exclude characters that could extend an identifier token
    # (letters, digits, +, #) but NOT '.', so a skill at the end of a sentence
    # ("… NLP.") still matches while "java" won't match inside "javascript".
    escaped = re.escape(skill)
    return re.compile(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)


_SKILL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (skill, _skill_pattern(skill)) for skill in ALL_SKILLS
]

_DEGREE_PATTERNS = [
    (re.compile(r"\bph\.?\s?d\b", re.I), "PhD"),
    (re.compile(r"\b(m\.?s\.?c?|master(?:'s)?|m\.?eng|mba)\b", re.I), "Master's"),
    (re.compile(r"\b(b\.?s\.?c?|bachelor(?:'s)?|b\.?eng|b\.?tech|b\.?a)\b", re.I), "Bachelor's"),
    (re.compile(r"\b(associate(?:'s)?|a\.?a\.?s?)\b", re.I), "Associate's"),
]

_FIELD_PATTERN = re.compile(
    r"\b(computer science|software engineering|data science|"
    r"electrical engineering|mathematics|statistics|information technology|"
    r"physics|information systems)\b",
    re.I,
)

# "5 years", "5+ years", "5 yrs of experience"
_YEARS_PATTERN = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs)", re.I)
# Date ranges like "2019 - 2023", "2019 – Present"
_RANGE_PATTERN = re.compile(
    r"(19|20)\d{2}\s*[-–—to]+\s*((?:19|20)\d{2}|present|current)", re.I
)


@dataclass
class Candidate:
    """A structured profile extracted from a resume."""

    name: str = "Unknown"
    raw_text: str = ""
    skills: list[str] = field(default_factory=list)
    years_experience: float = 0.0
    highest_degree: str | None = None
    field_of_study: str | None = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "years_experience": self.years_experience,
            "highest_degree": self.highest_degree,
            "field_of_study": self.field_of_study,
        }


def extract_skills(text: str) -> list[str]:
    """Return the sorted, canonicalized set of known skills present in text."""
    found: set[str] = set()
    for skill, pattern in _SKILL_PATTERNS:
        if pattern.search(text):
            found.add(canonical(skill))
    return sorted(found)


def extract_years_experience(text: str) -> float:
    """Estimate years of experience.

    Prefers an explicit statement ("5+ years"); otherwise sums the spans of
    dated employment ranges (capped, and treating 'present' as this year).
    """
    explicit = [int(m.group(1)) for m in _YEARS_PATTERN.finditer(text)]
    if explicit:
        return float(max(explicit))

    total = 0
    for m in _RANGE_PATTERN.finditer(text):
        start = int(m.group(0)[:4])
        end_token = m.group(2).lower()
        end = 2026 if end_token in {"present", "current"} else int(end_token)
        if end >= start:
            total += end - start
    return float(min(total, 45))


def extract_education(text: str) -> tuple[str | None, str | None]:
    """Return (highest_degree, field_of_study)."""
    highest = None
    for pattern, label in _DEGREE_PATTERNS:  # ordered PhD -> Master -> Bachelor
        if pattern.search(text):
            highest = label
            break
    field_match = _FIELD_PATTERN.search(text)
    field_of_study = field_match.group(1).title() if field_match else None
    return highest, field_of_study


def _guess_name(text: str) -> str:
    """Best-effort: the first non-empty line that looks like a name."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(w[:1].isupper() for w in words if w[:1].isalpha()):
            if "@" not in line and not any(ch.isdigit() for ch in line):
                return line
        break
    return "Unknown"


def extract_resume(text: str, name: str | None = None) -> Candidate:
    """Run the full extraction pipeline on a block of resume text."""
    degree, field_of_study = extract_education(text)
    return Candidate(
        name=name or _guess_name(text),
        raw_text=text,
        skills=extract_skills(text),
        years_experience=extract_years_experience(text),
        highest_degree=degree,
        field_of_study=field_of_study,
    )


def extract_text_from_pdf(path: str) -> str:
    """Extract text from a PDF resume (optional dependency: pdfplumber)."""
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install pdfplumber to parse PDF resumes: pip install pdfplumber") from exc
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)
