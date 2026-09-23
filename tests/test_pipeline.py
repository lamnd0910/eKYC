import numpy as np

from ekyc.common.config import PipelineSettings
from ekyc.common.types import PipelineContext, StageResult
from ekyc.pipeline import EkycPipeline


class FakeStage:
    def __init__(self, name: str, result: StageResult) -> None:
        self.name = name
        self._result = result
        self.calls = 0

    def run(self, ctx: PipelineContext) -> StageResult:
        self.calls += 1
        return self._result


def _settings() -> PipelineSettings:
    return PipelineSettings.model_validate(
        {
            "face_match": {"manual_review_low": 0.55, "manual_review_high": 0.75},
            "ocr_confidence": {"manual_review_low": 0.70, "manual_review_high": 0.90},
        }
    )


def _context() -> PipelineContext:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    return PipelineContext(id_front=image, selfie=image)


def test_pipeline_accepts_when_all_scores_are_certain() -> None:
    stages = [
        FakeStage("ocr", StageResult("ocr", True, "warning", scores={"ocr_confidence": 0.95})),
        FakeStage("face", StageResult("face", True, "warning", scores={"face_match": 0.90})),
    ]

    decision = EkycPipeline(stages, _settings()).verify(_context())

    assert decision.status == "ACCEPT"
    assert len(decision.stage_results) == 2
    assert all(result.latency_ms >= 0 for result in decision.stage_results)


def test_pipeline_rejects_and_stops_at_blocking_failure() -> None:
    rejected = FakeStage(
        "quality", StageResult("quality", False, "blocking", reasons=["image is blurred"])
    )
    not_run = FakeStage("ocr", StageResult("ocr", True, "warning"))

    decision = EkycPipeline([rejected, not_run], _settings()).verify(_context())

    assert decision.status == "REJECT"
    assert decision.reasons == ["image is blurred"]
    assert not_run.calls == 0


def test_pipeline_sends_uncertain_score_to_manual_review() -> None:
    stage = FakeStage("face", StageResult("face", True, "warning", scores={"face_match": 0.60}))

    decision = EkycPipeline([stage], _settings()).verify(_context())

    assert decision.status == "MANUAL_REVIEW"
    assert "face match score requires manual review" in decision.reasons
