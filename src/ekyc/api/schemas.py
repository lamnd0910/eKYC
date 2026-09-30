"""Pydantic schemas for public eKYC API responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ekyc.common.reasons import REASON_MESSAGES, ReasonCode
from ekyc.common.types import Decision, StageResult


class ReasonResponse(BaseModel):
    """Stable code and non-sensitive explanation."""

    code: ReasonCode
    message: str

    @classmethod
    def from_code(cls, code: ReasonCode) -> ReasonResponse:
        """Describe a reason without embedding request values."""
        return cls(code=code, message=REASON_MESSAGES[code])


class StageResultResponse(BaseModel):
    """JSON-safe representation of an individual stage result."""

    name: str
    outcome: Literal["PASSED", "FAILED", "NOT_EVALUATED"]
    severity: Literal["blocking", "warning"]
    reasons: list[ReasonResponse]
    scores: dict[str, float]
    latency_ms: float

    @classmethod
    def from_domain(cls, result: StageResult) -> StageResultResponse:
        """Map a domain result to its response schema."""
        return cls(
            name=result.name,
            outcome=result.outcome,
            severity=result.severity,
            reasons=[ReasonResponse.from_code(code) for code in result.reasons],
            scores=result.scores,
            latency_ms=result.latency_ms,
        )


class DecisionResponse(BaseModel):
    """Public decision returned by ``POST /v1/verify``."""

    status: Literal["ACCEPT", "REJECT", "MANUAL_REVIEW"]
    reasons: list[ReasonResponse]
    fields: dict[str, Any]
    stage_results: list[StageResultResponse]
    total_latency_ms: float = Field(ge=0.0)

    @classmethod
    def from_domain(cls, decision: Decision) -> DecisionResponse:
        """Map a pipeline decision to the API contract."""
        return cls(
            status=decision.status,
            reasons=[ReasonResponse.from_code(code) for code in decision.reasons],
            fields=decision.fields,
            stage_results=[
                StageResultResponse.from_domain(item) for item in decision.stage_results
            ],
            total_latency_ms=decision.total_latency_ms,
        )


class HealthResponse(BaseModel):
    """Liveness information and versions of configured models."""

    status: Literal["ok", "not_ready"]
    service_version: str
    model_versions: dict[str, str]
    not_evaluated_stages: list[str]
