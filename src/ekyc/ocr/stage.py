"""OCR stage contract."""

from ekyc.common.types import PipelineContext, StageResult


class OcrStage:
    """Extract ID fields from the rectified document.

    Input: rectified BGR uint8 document image, conventionally in the detection
    result, with shape ``(H, W, 3)``. Output: a ``StageResult`` with
    ``ocr_confidence`` and ``data['fields']`` for ID number, name, and birth
    date. A future implementation can detect text regions then recognize them.
    """

    name = "ocr"

    def run(self, ctx: PipelineContext) -> StageResult:
        """Recognize and structurally validate document text fields."""
        raise NotImplementedError("TODO: implement OCR extraction and validation")
