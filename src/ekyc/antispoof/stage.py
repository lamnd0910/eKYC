"""Anti-spoofing stage contract."""

from ekyc.common.types import PipelineContext, StageResult


class AntiSpoofStage:
    """Detect presentation attacks in the selfie.

    Input: ``ctx.selfie`` is a BGR uint8 image of shape ``(H, W, 3)``. Output:
    a ``StageResult`` with a spoof/liveness score. A future model may consume a
    normalized tensor of shape ``(1, 3, H, W)`` and calibrate its confidence.
    """

    name = "antispoof"

    def run(self, ctx: PipelineContext) -> StageResult:
        """Infer selfie liveness and flag print/screen replays."""
        raise NotImplementedError("TODO: implement anti-spoofing inference")
