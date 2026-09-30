"""Contracts shared by all eKYC pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import numpy as np

from ekyc.common.reasons import ReasonCode

Severity = Literal["blocking", "warning"]
DecisionStatus = Literal["ACCEPT", "REJECT", "MANUAL_REVIEW"]
StageOutcome = Literal["PASSED", "FAILED", "NOT_EVALUATED"]


@dataclass(slots=True)
class StageResult:
    """The normalized result produced by a pipeline stage.

    Attributes:
        name: Stable stage identifier.
        outcome: PASSED when a result exists, FAILED only when no result can be
            produced (for example, no document or face), or NOT_EVALUATED when
            the check has not run. Numeric decision thresholds belong to the
            pipeline, never to a stage.
        severity: Failure impact; only a FAILED ``blocking`` result stops the pipeline.
        reasons: Stable, non-sensitive reason codes.
        scores: Named numeric scores such as ``ocr_confidence`` or ``face_match``.
        data: Internal data for communication between stages, including OCR ``fields``.
        latency_ms: Stage execution time, measured by the pipeline.
    """

    name: str
    outcome: StageOutcome
    severity: Severity
    reasons: list[ReasonCode] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass(slots=True)
class PipelineContext:
    """Input images and accumulated results passed between stages.

    ``id_front`` and ``selfie`` are BGR, uint8 NumPy arrays with shape
    ``(height, width, 3)``. Stages may read previous results but must not log raw
    pixel data or document identifiers. All image artefacts exist for one
    request only; they must never be cached, logged, or serialized.
    """

    id_front: np.ndarray
    selfie: np.ndarray
    stage_results: dict[str, StageResult] = field(default_factory=dict)
    rectified_document: np.ndarray | None = None
    document_face: np.ndarray | None = None
    selfie_face: np.ndarray | None = None


class Stage(Protocol):
    """Interface implemented by every sequential pipeline stage."""

    name: str
    implemented: bool

    def run(self, ctx: PipelineContext) -> StageResult:
        """Run the stage using input and preceding stage results."""


@dataclass(slots=True)
class Decision:
    """Final eKYC decision returned by the pipeline and API."""

    status: DecisionStatus
    reasons: list[ReasonCode]
    fields: dict[str, Any]
    stage_results: list[StageResult]
    total_latency_ms: float
