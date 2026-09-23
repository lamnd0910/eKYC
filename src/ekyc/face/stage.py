"""Face-matching stage contract."""

from ekyc.common.types import PipelineContext, StageResult


class FaceMatchingStage:
    """Compare face embeddings from document and selfie.

    Input: document/selfie BGR uint8 images with shape ``(H, W, 3)``. Output:
    a ``StageResult`` with ``face_match`` similarity. A future implementation
    can detect/align faces, produce tensors ``(1, 3, 112, 112)``, then compare
    normalized embedding vectors.
    """

    name = "face"

    def run(self, ctx: PipelineContext) -> StageResult:
        """Detect, embed, and compare faces from document and selfie."""
        raise NotImplementedError("TODO: implement face detection and matching")
