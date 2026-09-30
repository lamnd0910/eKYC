"""Face-matching stage contract."""

from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult


class FaceMatchingStage:
    """Compare face embeddings from document and selfie.

    Input: document/selfie BGR uint8 images with shape ``(H, W, 3)``. Output:
    a ``StageResult`` with ``face_match`` similarity. A future implementation
    can detect/align faces, produce tensors ``(1, 3, 112, 112)``, then compare
    normalized embedding vectors.
    """

    name = "face"
    implemented = False

    def run(self, ctx: PipelineContext) -> StageResult:
        """Return an explicit pending result until ``_evaluate`` is implemented.

        TODO: Call ``_evaluate(ctx)`` when the ML work is complete.
        """
        return StageResult(self.name, "NOT_EVALUATED", "blocking", [ReasonCode.STAGE_NOT_EVALUATED])

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Detect BGR uint8 faces (H,W,3), then compare (1,3,112,112) tensors.

        Set ``ctx.document_face`` and ``ctx.selfie_face`` and return similarity;
        report FAILED only if a required face cannot be found.
        """
        raise NotImplementedError("TODO: implement face detection and matching")
