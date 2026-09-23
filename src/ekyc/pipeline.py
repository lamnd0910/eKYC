"""Sequential eKYC pipeline orchestration and decision rules."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from time import perf_counter

from ekyc.common.config import PipelineSettings
from ekyc.common.types import Decision, PipelineContext, Stage, StageResult


class EkycPipeline:
    """Run configured stages in order and apply model-independent policy.

    A failed blocking stage ends execution immediately. Warning failures are
    preserved in the response, while OCR and face uncertainty ranges are
    evaluated only after all required stages have completed.
    """

    def __init__(self, stages: Iterable[Stage], settings: PipelineSettings) -> None:
        self._stages = tuple(stages)
        self._settings = settings

    def verify(self, ctx: PipelineContext) -> Decision:
        """Execute stages, measure latency, and construct the final decision."""
        started_at = perf_counter()
        reasons: list[str] = []

        for stage in self._stages:
            stage_started_at = perf_counter()
            result = stage.run(ctx)
            latency_ms = (perf_counter() - stage_started_at) * 1000
            if result.name != stage.name:
                raise ValueError(f"Stage '{stage.name}' returned a result named '{result.name}'")
            measured_result = replace(result, latency_ms=latency_ms)
            ctx.stage_results[stage.name] = measured_result
            reasons.extend(measured_result.reasons)

            if not measured_result.passed and measured_result.severity == "blocking":
                return Decision(
                    status="REJECT",
                    reasons=reasons,
                    fields=self._extract_fields(ctx.stage_results),
                    stage_results=list(ctx.stage_results.values()),
                    total_latency_ms=(perf_counter() - started_at) * 1000,
                )

        status, decision_reasons = self._decide(ctx.stage_results)
        reasons.extend(decision_reasons)
        return Decision(
            status=status,
            reasons=reasons,
            fields=self._extract_fields(ctx.stage_results),
            stage_results=list(ctx.stage_results.values()),
            total_latency_ms=(perf_counter() - started_at) * 1000,
        )

    def _decide(self, results: dict[str, StageResult]) -> tuple[str, list[str]]:
        """Apply score-based manual-review rules from the typed configuration."""
        review_reasons: list[str] = []
        face_score = self._find_score(results, "face_match")
        if face_score is not None and self._settings.face_match.contains(face_score):
            review_reasons.append("face match score requires manual review")

        ocr_score = self._find_score(results, "ocr_confidence")
        if ocr_score is not None and self._settings.ocr_confidence.contains(ocr_score):
            review_reasons.append("OCR confidence requires manual review")

        if review_reasons:
            return "MANUAL_REVIEW", review_reasons
        return "ACCEPT", []

    @staticmethod
    def _find_score(results: dict[str, StageResult], score_name: str) -> float | None:
        """Return a named score from the first stage that supplies it."""
        for result in results.values():
            score = result.scores.get(score_name)
            if score is not None:
                return score
        return None

    @staticmethod
    def _extract_fields(results: dict[str, StageResult]) -> dict[str, object]:
        """Expose only the OCR fields mapping in the external decision payload."""
        ocr_result = results.get("ocr")
        if ocr_result is None:
            return {}
        fields = ocr_result.data.get("fields", {})
        return dict(fields) if isinstance(fields, dict) else {}
