"""Run the ranking accuracy evaluation and print the report."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.evaluate import evaluate  # noqa: E402

if __name__ == "__main__":
    evaluate()
