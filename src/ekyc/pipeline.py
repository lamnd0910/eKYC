"""Sequential eKYC pipeline orchestration and decision rules."""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable
from dataclasses import replace
from time import perf_counter

from ekyc.common.config import PipelineSettings, ScoreZone
from ekyc.common.reasons import ReasonCode
from ekyc.common.types import Decision, DecisionStatus, PipelineContext, Stage, StageResult

logger = logging.getLogger(__name__)


class StageExecutionError(Exception):
    """Unexpected failure within a named verification stage."""

    def __init__(self, stage_name: str) -> None:
        self.stage_name = stage_name
        super().__init__(stage_name)


class EkycPipeline:
    """Run configured stages in order and apply model-independent policy.

    A blocking FAILED stage ends execution immediately. Other outcomes are
    accumulated before completeness and score rules are applied.
    """

    def __init__(self, stages: Iterable[Stage], settings: PipelineSettings) -> None:
        self._stages = tuple(stages)
        self._settings = settings

    @property
    def not_evaluated_stages(self) -> list[str]:
        """Report known stubs without processing an image."""
        return [stage.name for stage in self._stages if not stage.implemented]

    def verify(self, ctx: PipelineContext) -> Decision:
        """Execute stages, measure latency, and construct the final decision."""
        started_at = perf_counter()
        reasons: list[ReasonCode] = []

        for stage in self._stages:
            stage_started_at = perf_counter()
            try:
                result = stage.run(ctx)
                if result.name != stage.name:
                    raise ValueError("Stage result name does not match its stage")
            except Exception as exc:
                logger.error("Stage %s raised %s", stage.name, type(exc).__name__)
                raise StageExecutionError(stage.name) from exc
            latency_ms = (perf_counter() - stage_started_at) * 1000
            measured_result = replace(result, latency_ms=latency_ms)
            ctx.stage_results[stage.name] = measured_result
            reasons.extend(measured_result.reasons)

            if measured_result.outcome == "FAILED" and measured_result.severity == "blocking":
                if not measured_result.reasons:
                    reasons.append(ReasonCode.STAGE_FAILED)
                return Decision(
                    status="REJECT",
                    reasons=list(dict.fromkeys(reasons)),
                    fields=self._extract_fields(ctx.stage_results),
                    stage_results=list(ctx.stage_results.values()),
                    total_latency_ms=(perf_counter() - started_at) * 1000,
                )

        status, decision_reasons = self._decide(ctx.stage_results)
        reasons.extend(decision_reasons)
        return Decision(
            status=status,
            reasons=list(dict.fromkeys(reasons)),
            fields=self._extract_fields(ctx.stage_results),
            stage_results=list(ctx.stage_results.values()),
            total_latency_ms=(perf_counter() - started_at) * 1000,
        )

    def _decide(self, results: dict[str, StageResult]) -> tuple[DecisionStatus, list[ReasonCode]]:
        """Require complete checks and scores before allowing acceptance."""
        review_reasons: list[ReasonCode] = []
        reject_reasons: list[ReasonCode] = []
        if any(result.outcome == "NOT_EVALUATED" for result in results.values()):
            review_reasons.append(ReasonCode.STAGE_NOT_EVALUATED)
        if any(name not in results for name in self._settings.required_stages):
            review_reasons.append(ReasonCode.REQUIRED_STAGE_MISSING)
        if any(result.outcome == "FAILED" for result in results.values()):
            review_reasons.append(ReasonCode.STAGE_FAILED)

        for stage_name, score_name, threshold, low_reason, uncertain_reason in (
            (
                "face",
                "face_match",
                self._settings.face_match,
                ReasonCode.FACE_MISMATCH,
                ReasonCode.FACE_MATCH_UNCERTAIN,
            ),
            (
                "ocr",
                "ocr_confidence",
                self._settings.ocr_confidence,
                ReasonCode.OCR_CONFIDENCE_LOW,
                ReasonCode.OCR_CONFIDENCE_UNCERTAIN,
            ),
        ):
            result = results.get(stage_name)
            if result is None or result.outcome != "PASSED":
                continue
            score = result.scores.get(score_name)
            if score is None or not math.isfinite(score):
                review_reasons.append(ReasonCode.REQUIRED_SCORE_MISSING)
            else:
                zone = threshold.classify(score)
                if zone == ScoreZone.BELOW:
                    if threshold.below_action == "REJECT":
                        reject_reasons.append(low_reason)
                    else:
                        review_reasons.append(low_reason)
                elif zone == ScoreZone.UNCERTAIN:
                    review_reasons.append(uncertain_reason)

        if reject_reasons:
            return "REJECT", reject_reasons + review_reasons
        if review_reasons:
            return "MANUAL_REVIEW", review_reasons
        return "ACCEPT", []

    @staticmethod
    def _extract_fields(results: dict[str, StageResult]) -> dict[str, object]:
        """Expose only the OCR fields mapping in the external decision payload."""
        ocr_result = results.get("ocr")
        if ocr_result is None or ocr_result.outcome != "PASSED":
            return {}
        fields = ocr_result.data.get("fields", {})
        return dict(fields) if isinstance(fields, dict) else {}
