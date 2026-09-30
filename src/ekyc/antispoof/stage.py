"""Anti-spoofing stage contract."""

from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult


class AntiSpoofStage:
    """Detect presentation attacks in the selfie.

    Input: ``ctx.selfie`` is a BGR uint8 image of shape ``(H, W, 3)``. Output:
    a ``StageResult`` with a spoof/liveness score. A future model may consume a
    normalized tensor of shape ``(1, 3, H, W)`` and calibrate its confidence.
    """

    name = "antispoof"
    implemented = False

    def run(self, ctx: PipelineContext) -> StageResult:
        """Return an explicit pending result until ``_evaluate`` is implemented.

        TODO: Call ``_evaluate(ctx)`` when the ML work is complete.
        """
        return StageResult(self.name, "NOT_EVALUATED", "warning", [ReasonCode.STAGE_NOT_EVALUATED])

    def _evaluate(self, ctx: PipelineContext) -> StageResult:
        """Score BGR uint8 selfie (H,W,3), possibly via tensor (1,3,H,W).

        Return a liveness score; policy thresholds belong to the pipeline.
        The document replay branch remains pending under D7 because suitable
        public data is unavailable. A replayed ID remains a risk. With licensed
        data, evaluate a separate document presentation-attack branch.
        """
        raise NotImplementedError("TODO: implement anti-spoofing inference")
