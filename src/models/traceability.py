"""Compatibility exports for traceability models.

Canonical semantics live in ``src.models.canonical``. New code should import there.
"""
from .canonical import ProductBatch, ChainOfCustodyLeg, Incident, CAPA, QCStatus
from src.jev.taxonomy import RootCauseStatus, IssueClass, ProcessStage

__all__ = [
    "ProductBatch", "ChainOfCustodyLeg", "Incident", "CAPA", "QCStatus",
    "RootCauseStatus", "IssueClass", "ProcessStage",
]
