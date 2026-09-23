"""Pydantic schemas for public eKYC API responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ekyc.common.types import Decision, StageResult


class StageResultResponse(BaseModel):
    """JSON-safe representation of an individual stage result."""

    name: str
    passed: bool
    severity: Literal["blocking", "warning"]
    reasons: list[str]
    scores: dict[str, float]
    data: dict[str, Any]
    latency_ms: float

    @classmethod
    def from_domain(cls, result: StageResult) -> StageResultResponse:
        """Map a domain result to its response schema."""
        return cls(
            name=result.name,
            passed=result.passed,
            severity=result.severity,
            reasons=result.reasons,
            scores=result.scores,
            data=result.data,
            latency_ms=result.latency_ms,
        )


class DecisionResponse(BaseModel):
    """Public decision returned by ``POST /v1/verify``."""

    status: Literal["ACCEPT", "REJECT", "MANUAL_REVIEW"]
    reasons: list[str]
    fields: dict[str, Any]
    stage_results: list[StageResultResponse]
    total_latency_ms: float = Field(ge=0.0)

    @classmethod
    def from_domain(cls, decision: Decision) -> DecisionResponse:
        """Map a pipeline decision to the API contract."""
        return cls(
            status=decision.status,
            reasons=decision.reasons,
            fields=decision.fields,
            stage_results=[
                StageResultResponse.from_domain(item) for item in decision.stage_results
            ],
            total_latency_ms=decision.total_latency_ms,
        )


class HealthResponse(BaseModel):
    """Liveness information and versions of configured models."""

    status: Literal["ok"]
    service_version: str
    model_versions: dict[str, str]
