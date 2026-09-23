"""Image-quality stage contract."""

from ekyc.common.types import PipelineContext, StageResult


class ImageQualityStage:
    """Assess document and selfie image usability.

    Input: BGR uint8 images in ``ctx`` with shape ``(H, W, 3)``. Output: a
    ``StageResult`` containing blur, glare, darkness and crop scores. A future
    implementation can combine image statistics with a learned quality model.
    """

    name = "quality"

    def run(self, ctx: PipelineContext) -> StageResult:
        """Measure blur, glare, exposure, and document cropping."""
        raise NotImplementedError("TODO: implement image quality assessment")
