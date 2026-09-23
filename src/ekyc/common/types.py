"""Contracts shared by all eKYC pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import numpy as np

Severity = Literal["blocking", "warning"]
DecisionStatus = Literal["ACCEPT", "REJECT", "MANUAL_REVIEW"]


@dataclass(slots=True)
class StageResult:
    """The normalized result produced by a pipeline stage.

    Attributes:
        name: Stable stage identifier.
        passed: Whether this stage met its own acceptance rule.
        severity: Failure impact; only a failed ``blocking`` result stops the pipeline.
        reasons: Human-readable, non-sensitive explanations.
        scores: Named numeric scores such as ``ocr_confidence`` or ``face_match``.
        data: Non-sensitive extracted/derived data, including optional OCR ``fields``.
        latency_ms: Stage execution time, measured by the pipeline.
    """

    name: str
    passed: bool
    severity: Severity
    reasons: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass(slots=True)
class PipelineContext:
    """Input images and accumulated results passed between stages.

    ``id_front`` and ``selfie`` are BGR, uint8 NumPy arrays with shape
    ``(height, width, 3)``. Stages may read previous results but must not log raw
    pixel data or document identifiers.
    """

    id_front: np.ndarray
    selfie: np.ndarray
    stage_results: dict[str, StageResult] = field(default_factory=dict)


class Stage(Protocol):
    """Interface implemented by every sequential pipeline stage."""

    name: str

    def run(self, ctx: PipelineContext) -> StageResult:
        """Run the stage using input and preceding stage results."""


@dataclass(slots=True)
class Decision:
    """Final eKYC decision returned by the pipeline and API."""

    status: DecisionStatus
    reasons: list[str]
    fields: dict[str, Any]
    stage_results: list[StageResult]
    total_latency_ms: float
