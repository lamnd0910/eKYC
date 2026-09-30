"""Face-matching stage contract."""

from ekyc.common.stage_results import not_evaluated_result
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
        """Return pending until ML work is complete.

        TODO: Set ``implemented`` to True after implementing ``_evaluate``.
        """
        if not self.implemented:
            return not_evaluated_result(self.name, "blocking")
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Detect BGR uint8 faces (H,W,3), then compare (1,3,112,112) tensors.

        Set ``ctx.document_face`` and ``ctx.selfie_face`` and return similarity;
        report FAILED only if a required face cannot be found.
        """
        raise NotImplementedError("TODO: implement face detection and matching")
