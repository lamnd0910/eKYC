"""OCR stage contract."""

from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult


class OcrStage:
    """Extract ID fields from the rectified document.

    Input: ``ctx.rectified_document`` BGR uint8 with shape ``(H, W, 3)``.
    Output: a ``StageResult`` with
    ``ocr_confidence`` and ``data['fields']`` for ID number, name, and birth
    date. A future implementation can detect text regions then recognize them.
    """

    name = "ocr"
    implemented = False

    def run(self, ctx: PipelineContext) -> StageResult:
        """Return pending until ML work is complete.

        TODO: Set ``implemented`` to True after implementing ``_evaluate``.
        """
        if not self.implemented:
            return StageResult(
                self.name, "NOT_EVALUATED", "warning", [ReasonCode.STAGE_NOT_EVALUATED]
            )
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Extract fields and confidence from BGR uint8 document (H,W,3).

        Return OCR fields in internal data and rule violations as reason codes.
        """
        raise NotImplementedError("TODO: implement OCR extraction and validation")
