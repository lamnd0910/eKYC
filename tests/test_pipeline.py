"""Decision-policy tests using synthetic arrays and fake stages."""

from itertools import product

import numpy as np
import pytest

from ekyc.common.config import PipelineSettings
from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult
from ekyc.pipeline import EkycPipeline, StageExecutionError

STAGE_NAMES = ("detection", "quality", "antispoof", "ocr", "face")


class FakeStage:
    def __init__(self, result: StageResult) -> None:
        self.name = result.name
        self.result = result
        self.calls = 0

    def run(self, ctx: PipelineContext) -> StageResult:
        self.calls += 1
        return self.result


def _settings() -> PipelineSettings:
    return PipelineSettings.model_validate(
        {
            "required_stages": list(STAGE_NAMES),
            "face_match": {"manual_review_low": 0.55, "manual_review_high": 0.75},
            "ocr_confidence": {"manual_review_low": 0.70, "manual_review_high": 0.90},
        }
    )


def _context() -> PipelineContext:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    return PipelineContext(id_front=image, selfie=image)


def _stage(name: str, outcome: str, severity: str = "warning") -> FakeStage:
    scores = {}
    if outcome == "PASSED" and name == "ocr":
        scores = {"ocr_confidence": 0.95}
    if outcome == "PASSED" and name == "face":
        scores = {"face_match": 0.95}
    reasons = [ReasonCode.STAGE_NOT_EVALUATED] if outcome == "NOT_EVALUATED" else []
    return FakeStage(StageResult(name, outcome, severity, reasons=reasons, scores=scores))


@pytest.mark.parametrize("outcomes", product(("PASSED", "FAILED", "NOT_EVALUATED"), repeat=5))
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
    assert all(stage.calls == 0 for stage in stages[blocking_index + 1 :])


def test_blocking_failure_overrides_prior_not_evaluated_stage() -> None:
    stages = [_stage("detection", "NOT_EVALUATED"), _stage("quality", "FAILED", "blocking")]

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "REJECT"


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
    stages[-1].result.scores["face_match"] = 0.60

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert ReasonCode.FACE_MATCH_UNCERTAIN in decision.reasons


def test_unexpected_stage_error_is_sanitized(caplog: pytest.LogCaptureFixture) -> None:
    class BrokenStage:
        name = "detection"

        def run(self, ctx: PipelineContext) -> StageResult:
            raise ValueError("sensitive document number")

    with pytest.raises(StageExecutionError) as error:
        EkycPipeline([BrokenStage()], _settings()).verify(_context())

    assert error.value.stage_name == "detection"
    assert "ValueError" in caplog.text
    assert "sensitive document number" not in caplog.text
