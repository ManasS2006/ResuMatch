"""Evaluate ranking accuracy on the synthetic labeled dataset.

Method (kept honest):
  1. Generate balanced labeled (job, resume) pairs.
  2. Score every pair with the ranker.
  3. Split into train/test. Choose the decision threshold that maximizes
     accuracy on *train* only, then report metrics on the held-out *test* set.

Reporting a threshold tuned on training data but measured on unseen test data
avoids the classic "tuned on the same data I report" inflation.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config
from .dataset import generate_dataset
from .extract import extract_resume
from .rank import parse_job, rank


@dataclass
class EvalResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    threshold: float
    n_test: int
    default_threshold_accuracy: float

    def as_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "chosen_threshold": round(self.threshold, 3),
            "n_test": self.n_test,
            "accuracy_at_default_threshold": round(self.default_threshold_accuracy, 4),
        }

    def __str__(self) -> str:
        return (
            f"accuracy={self.accuracy:.1%}  precision={self.precision:.1%}  "
            f"recall={self.recall:.1%}  f1={self.f1:.3f}  "
            f"(threshold={self.threshold:.2f}, n_test={self.n_test})"
        )


def _score_pairs(pairs) -> list[tuple[float, int]]:
    """Return (score, label) for each pair."""
    scored = []
    for p in pairs:
        job = parse_job(p.job_text)
        candidate = extract_resume(p.resume_text)
        result = rank(job, [candidate])[0]
        scored.append((result.total, p.label))
    return scored


def _metrics(scored: list[tuple[float, int]], threshold: float) -> tuple[float, float, float, float]:
    tp = fp = tn = fn = 0
    for score, label in scored:
        pred = 1 if score >= threshold else 0
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return accuracy, precision, recall, f1


def evaluate(n: int = 1000, seed: int = config.RANDOM_SEED, verbose: bool = True) -> EvalResult:
    pairs = generate_dataset(n=n, seed=seed)
    scored = _score_pairs(pairs)

    split = int(len(scored) * 0.7)
    train, test = scored[:split], scored[split:]

    # Choose the threshold that maximizes accuracy on the training split.
    best_t, best_acc = config.MATCH_THRESHOLD, -1.0
    for i in range(1, 100):
        t = i / 100
        acc, *_ = _metrics(train, t)
        if acc > best_acc:
            best_acc, best_t = acc, t

    accuracy, precision, recall, f1 = _metrics(test, best_t)
    default_acc, *_ = _metrics(test, config.MATCH_THRESHOLD)

    result = EvalResult(
        accuracy=accuracy, precision=precision, recall=recall, f1=f1,
        threshold=best_t, n_test=len(test), default_threshold_accuracy=default_acc,
    )
    if verbose:
        print(f"Dataset: {len(pairs)} pairs  (train={len(train)}, test={len(test)})")
        print(f"Best threshold on train: {best_t:.2f}")
        print(f"Test metrics: {result}")
        print(f"Accuracy at default threshold ({config.MATCH_THRESHOLD}): {default_acc:.1%}")
    return result


if __name__ == "__main__":
    evaluate()
