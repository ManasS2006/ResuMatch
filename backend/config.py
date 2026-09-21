"""Configuration for extraction and ranking."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Ranking weights (sum to 1.0) ------------------------------------------
# The final match score is a weighted blend of three signals.
WEIGHT_SKILLS = 0.60        # overlap between required and candidate skills
WEIGHT_SIMILARITY = 0.25    # TF-IDF cosine similarity of full texts
WEIGHT_EXPERIENCE = 0.15    # whether candidate meets required years

# A candidate scoring at or above this is predicted a "match". 0.60 is the value
# selected by the evaluation's train-split threshold search (see backend/evaluate.py).
MATCH_THRESHOLD = 0.60

# Reproducibility for the synthetic evaluation dataset.
RANDOM_SEED = 42
