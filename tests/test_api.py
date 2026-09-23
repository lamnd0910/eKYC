from fastapi.testclient import TestClient

from ekyc.api.deps import get_pipeline
from ekyc.api.main import app
from ekyc.common.config import PipelineSettings
from ekyc.common.types import StageResult
from ekyc.pipeline import EkycPipeline


class PassingStage:
    name = "ocr"

    def run(self, ctx: object) -> StageResult:
        return StageResult(
            name=self.name,
            passed=True,
            severity="warning",
            scores={"ocr_confidence": 0.99},
            data={"fields": {"full_name": "Synthetic User"}},
        )


def test_verify_accepts_synthetic_multipart_images(synthetic_image_bytes: bytes) -> None:
    settings = PipelineSettings.model_validate(
        {
            "face_match": {"manual_review_low": 0.55, "manual_review_high": 0.75},
            "ocr_confidence": {"manual_review_low": 0.70, "manual_review_high": 0.90},
        }
    )
    app.dependency_overrides[get_pipeline] = lambda: EkycPipeline([PassingStage()], settings)
    client = TestClient(app)

    try:
        response = client.post(
            "/v1/verify",
            files={
                "id_front": ("id.png", synthetic_image_bytes, "image/png"),
                "selfie": ("selfie.png", synthetic_image_bytes, "image/png"),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPT"
    assert response.json()["fields"]["full_name"] == "Synthetic User"


def test_health_reports_configured_versions() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
