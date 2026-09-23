"""Document-detection stage contract."""

from ekyc.common.types import PipelineContext, StageResult


class DocumentDetectionStage:
    """Locate and rectify the ID document.

    Input: ``ctx.id_front`` is BGR uint8 with shape ``(H, W, 3)``.
    Output: a ``StageResult`` whose data should contain rectified BGR image
    ``(H2, W2, 3)`` and four document corners. A future implementation can use
    a corner detector followed by OpenCV perspective transformation.
    """

    name = "detection"

    def run(self, ctx: PipelineContext) -> StageResult:
        """Run document localization and perspective normalization."""
        raise NotImplementedError("TODO: implement document corner detection and rectification")
