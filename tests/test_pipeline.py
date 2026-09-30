"""Decision-policy tests using synthetic arrays and fake stages."""

from itertools import product
from pathlib import Path

import numpy as np
import pytest

from ekyc.antispoof.stage import AntiSpoofStage
from ekyc.common.config import PipelineSettings, load_pipeline_settings
from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, Stage, StageResult
from ekyc.detection.stage import DocumentDetectionStage
from ekyc.face.stage import FaceMatchingStage
from ekyc.ocr.stage import OcrStage
from ekyc.pipeline import EkycPipeline, StageExecutionError
from ekyc.quality.stage import ImageQualityStage

STAGE_NAMES = ("detection", "quality", "antispoof", "ocr", "face")
SETTINGS = load_pipeline_settings(Path(__file__).resolve().parents[1] / "configs/pipeline.yaml")


class FakeStage:
    def __init__(self, result: StageResult) -> None:
        self.name = result.name
        self.implemented = True
        self.result = result
        self.calls = 0

    def run(self, ctx: PipelineContext) -> StageResult:
        self.calls += 1
        return self.result


def _settings() -> PipelineSettings:
    return SETTINGS


def _context() -> PipelineContext:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    return PipelineContext(id_front=image, selfie=image)


def _stage(name: str, outcome: str, severity: str = "warning") -> FakeStage:
    scores = {}
    if outcome == "PASSED" and name == "ocr":
        scores = {"ocr_confidence": SETTINGS.ocr_confidence.manual_review_high}
    if outcome == "PASSED" and name == "face":
        scores = {"face_match": SETTINGS.face_match.manual_review_high}
    reasons = [ReasonCode.STAGE_NOT_EVALUATED] if outcome == "NOT_EVALUATED" else []
    return FakeStage(StageResult(name, outcome, severity, reasons=reasons, scores=scores))


@pytest.mark.parametrize(
    "outcomes", tuple(product(("PASSED", "FAILED", "NOT_EVALUATED"), repeat=5))
)
def test_every_outcome_combination_is_fail_closed(outcomes: tuple[str, ...]) -> None:
    stages = [_stage(name, outcome) for name, outcome in zip(STAGE_NAMES, outcomes, strict=True)]

    decision = EkycPipeline(stages, _settings()).verify(_context())

    expected = "ACCEPT" if all(outcome == "PASSED" for outcome in outcomes) else "MANUAL_REVIEW"
    assert decision.status == expected
    if "NOT_EVALUATED" in outcomes:
        assert decision.status != "ACCEPT"
        assert all(stage.calls == 1 for stage in stages)


@pytest.mark.parametrize("blocking_index", range(5))
def test_blocking_failed_rejects_early(blocking_index: int) -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    stages[blocking_index] = _stage(STAGE_NAMES[blocking_index], "FAILED", "blocking")

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "REJECT"
    assert ReasonCode.STAGE_FAILED in decision.reasons
    assert all(stage.calls == 0 for stage in stages[blocking_index + 1 :])


def test_blocking_failure_overrides_prior_not_evaluated_stage() -> None:
    stages = [_stage("detection", "NOT_EVALUATED"), _stage("quality", "FAILED", "blocking")]

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "REJECT"
    assert ReasonCode.STAGE_FAILED in decision.reasons


@pytest.mark.parametrize("stage_name", ("face", "ocr"))
@pytest.mark.parametrize("point", ("below", "at_low", "between", "at_high", "above"))
def test_score_regions_follow_d15(stage_name: str, point: str) -> None:
    settings = _settings()
    threshold = getattr(settings, "face_match" if stage_name == "face" else "ocr_confidence")
    low, high = threshold.manual_review_low, threshold.manual_review_high
    score = {
        "below": low / 2,
        "at_low": low,
        "between": (low + high) / 2,
        "at_high": high,
        "above": (high + 1) / 2,
    }[point]
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    target = next(stage for stage in stages if stage.name == stage_name)
    target.result.scores["face_match" if stage_name == "face" else "ocr_confidence"] = score

    decision = EkycPipeline(stages, settings).verify(_context())

    if point == "below":
        expected_status = "REJECT" if stage_name == "face" else "MANUAL_REVIEW"
        expected_reason = (
            ReasonCode.FACE_MISMATCH if stage_name == "face" else ReasonCode.OCR_CONFIDENCE_LOW
        )
    elif point in ("at_low", "between"):
        expected_status = "MANUAL_REVIEW"
        expected_reason = (
            ReasonCode.FACE_MATCH_UNCERTAIN
            if stage_name == "face"
            else ReasonCode.OCR_CONFIDENCE_UNCERTAIN
        )
    else:
        expected_status = "ACCEPT"
        expected_reason = None
    assert decision.status == expected_status
    assert decision.reasons == ([expected_reason] if expected_reason is not None else [])


def test_face_mismatch_overrides_not_evaluated() -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    stages[1] = _stage("quality", "NOT_EVALUATED")
    stages[-1].result.scores["face_match"] = _settings().face_match.manual_review_low / 2

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "REJECT"
    assert ReasonCode.FACE_MISMATCH in decision.reasons
    assert ReasonCode.STAGE_NOT_EVALUATED in decision.reasons
    assert len(decision.reasons) == len(set(decision.reasons))


def test_low_ocr_with_good_face_requires_manual_review() -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    stages[-2].result.scores["ocr_confidence"] = _settings().ocr_confidence.manual_review_low / 2

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert ReasonCode.OCR_CONFIDENCE_LOW in decision.reasons


@pytest.mark.parametrize("outcome", ("FAILED", "NOT_EVALUATED"))
def test_ocr_fields_are_hidden_unless_passed(outcome: str) -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    stages[-2] = _stage("ocr", outcome)
    stages[-2].result.data = {"fields": {"document_number": "synthetic"}}

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.fields == {}


@pytest.mark.parametrize(
    "stage_class",
    (DocumentDetectionStage, ImageQualityStage, AntiSpoofStage, OcrStage, FaceMatchingStage),
)
def test_implemented_stage_calls_evaluate(
    stage_class: type[Stage], monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def fake_evaluate(self: Stage, ctx: PipelineContext) -> StageResult:
        nonlocal called
        called = True
        return StageResult(self.name, "PASSED", "warning")

    monkeypatch.setattr(stage_class, "implemented", True)
    monkeypatch.setattr(stage_class, "_evaluate", fake_evaluate)
    stage = stage_class()

    assert stage.run(_context()).outcome == "PASSED"
    assert called
    assert EkycPipeline([stage], _settings()).not_evaluated_stages == []


def test_missing_required_stage_cannot_accept() -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES if name != "quality"]

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert ReasonCode.REQUIRED_STAGE_MISSING in decision.reasons


@pytest.mark.parametrize("missing_score_stage", ("ocr", "face"))
def test_passed_stage_without_required_score_cannot_accept(missing_score_stage: str) -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    next(stage for stage in stages if stage.name == missing_score_stage).result.scores.clear()

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert ReasonCode.REQUIRED_SCORE_MISSING in decision.reasons


def test_uncertain_score_requires_review() -> None:
    stages = [_stage(name, "PASSED") for name in STAGE_NAMES]
    threshold = _settings().face_match
    stages[-1].result.scores["face_match"] = (
        threshold.manual_review_low + threshold.manual_review_high
    ) / 2

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert ReasonCode.FACE_MATCH_UNCERTAIN in decision.reasons


def test_unexpected_stage_error_is_sanitized(caplog: pytest.LogCaptureFixture) -> None:
    class BrokenStage:
        name = "detection"
        implemented = True

        def run(self, ctx: PipelineContext) -> StageResult:
            raise ValueError("sensitive document number")

    with pytest.raises(StageExecutionError) as error:
        EkycPipeline([BrokenStage()], _settings()).verify(_context())

    assert error.value.stage_name == "detection"
    assert "ValueError" in caplog.text
    assert "sensitive document number" not in caplog.text
