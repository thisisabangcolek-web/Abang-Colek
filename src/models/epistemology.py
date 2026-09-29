"""Compatibility exports for epistemology models.

Canonical semantics live in ``src.models.canonical``. New code should import there.
"""
from .canonical import Evidence, ObservedFact, Fact, StructuredClassification, Inference, Hypothesis, Claim, HypothesisStatus

__all__ = [
    "Evidence", "ObservedFact", "Fact", "StructuredClassification",
    "Inference", "Hypothesis", "Claim", "HypothesisStatus",
]
