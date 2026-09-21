"""AI-Powered Resume Screener.

An NLP pipeline that extracts skills, experience, and education from resumes,
plus a ranking algorithm that matches candidates to a job description.
"""
import sys as _sys
from pathlib import Path as _Path

# Make the top-level `data` package (the skills gazetteer) importable whenever
# `backend` is imported, regardless of the current working directory.
_repo_root = str(_Path(__file__).resolve().parent.parent)
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)

__version__ = "0.1.0"
