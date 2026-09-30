"""Shared constructors for stage outcomes."""

from ekyc.common.reasons import ReasonCode
from ekyc.common.types import Severity, StageResult


def not_evaluated_result(name: str, severity: Severity) -> StageResult:
    """Return a pending stage result without inventing scores or data."""
    return StageResult(name, "NOT_EVALUATED", severity, [ReasonCode.STAGE_NOT_EVALUATED])
