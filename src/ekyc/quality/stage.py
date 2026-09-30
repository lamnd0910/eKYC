"""Image-quality stage contract."""

from ekyc.common.stage_results import not_evaluated_result
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
        """Return pending until ML work is complete.

        TODO: Set ``implemented`` to True after implementing ``_evaluate``.
        """
        if not self.implemented:
            return not_evaluated_result(self.name, "warning")
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Measure blur, glare, exposure, and crop for BGR uint8 (H,W,3) images.

        Return raw quality scores in a StageResult; pipeline owns thresholds.
        """
        raise NotImplementedError("TODO: implement image quality assessment")
