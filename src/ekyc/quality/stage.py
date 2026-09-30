"""Image-quality stage contract."""

from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult


class ImageQualityStage:
    """Assess document and selfie image usability.

    Input: BGR uint8 images in ``ctx`` with shape ``(H, W, 3)``. Output: a
    ``StageResult`` containing blur, glare, darkness and crop scores. A future
    implementation can combine image statistics with a learned quality model.
    """

    name = "quality"
    implemented = False

    def run(self, ctx: PipelineContext) -> StageResult:
        """Return an explicit pending result until ``_evaluate`` is implemented.

        TODO: Call ``_evaluate(ctx)`` when the ML work is complete.
        """
        return StageResult(self.name, "NOT_EVALUATED", "warning", [ReasonCode.STAGE_NOT_EVALUATED])

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Measure blur, glare, exposure, and crop for BGR uint8 (H,W,3) images.

        Return raw quality scores in a StageResult; pipeline owns thresholds.
        """
        raise NotImplementedError("TODO: implement image quality assessment")
