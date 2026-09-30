"""Document-detection stage contract."""

from ekyc.common.stage_results import not_evaluated_result
from ekyc.common.types import PipelineContext, StageResult


class DocumentDetectionStage:
    """Locate and rectify the ID document.

    Input: ``ctx.id_front`` is BGR uint8 with shape ``(H, W, 3)``.
    Output: a ``StageResult`` and ``ctx.rectified_document`` BGR uint8 image
    ``(H2, W2, 3)`` with four document corners in internal data. It can use
    a corner detector followed by OpenCV perspective transformation.
    """

    name = "detection"
    implemented = False

    def run(self, ctx: PipelineContext) -> StageResult:
        """Return pending until ML work is complete.

        TODO: Set ``implemented`` to True after implementing ``_evaluate``.
        """
        if not self.implemented:
            return not_evaluated_result(self.name, "blocking")
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Rectify BGR uint8 ``ctx.id_front`` (H,W,3) into (H2,W2,3).

        Set ``ctx.rectified_document`` and return corners and detection scores;
        report FAILED only when no document can be located.
        """
        raise NotImplementedError("TODO: implement document corner detection and rectification")
