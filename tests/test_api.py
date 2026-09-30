"""Public API contract and upload-boundary tests."""

import struct
import zlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from ekyc.api.deps import get_app_settings, get_pipeline
from ekyc.api.main import app
from ekyc.common.config import load_pipeline_settings
from ekyc.common.image_io import decode_bgr_image
from ekyc.common.reasons import ReasonCode
from ekyc.common.types import PipelineContext, StageResult
from ekyc.pipeline import EkycPipeline


class FakeStage:
    def __init__(self, name: str, outcome: str = "PASSED") -> None:
        self.name = name
        self.outcome = outcome
        self.implemented = True

    def run(self, ctx: PipelineContext) -> StageResult:
        scores = {"ocr_confidence": 0.99} if self.name == "ocr" else {}
        if self.name == "face":
            scores = {"face_match": 0.99}
        data = {"fields": {"full_name": "Synthetic User"}} if self.name == "ocr" else {}
        reasons = [ReasonCode.STAGE_NOT_EVALUATED] if self.outcome == "NOT_EVALUATED" else []
        return StageResult(self.name, self.outcome, "warning", reasons, scores, data)


def _pipeline(outcome: str = "PASSED") -> EkycPipeline:
    settings = load_pipeline_settings(Path(__file__).resolve().parents[1] / "configs/pipeline.yaml")
    names = ("detection", "quality", "antispoof", "ocr", "face")
    return EkycPipeline(
        [FakeStage(name, outcome if name == "quality" else "PASSED") for name in names], settings
    )


def _post(client: TestClient, image: bytes) -> object:
    return client.post(
        "/v1/verify",
        files={
            "id_front": ("id.png", image, "image/png"),
            "selfie": ("selfie.png", image, "image/png"),
        },
    )


def test_verify_response_excludes_internal_data(synthetic_image_bytes: bytes) -> None:
    app.dependency_overrides[get_pipeline] = lambda: _pipeline("NOT_EVALUATED")
    try:
        response = _post(TestClient(app), synthetic_image_bytes)
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "MANUAL_REVIEW"
    assert body["fields"] == {"full_name": "Synthetic User"}
    assert all("data" not in result for result in body["stage_results"])
    assert {"code", "message"} == set(body["reasons"][0])
    assert body["reasons"][0]["code"] == "STAGE_NOT_EVALUATED"
    assert body["stage_results"][1]["reasons"][0]["code"] == "STAGE_NOT_EVALUATED"


def test_complete_synthetic_pipeline_accepts(synthetic_image_bytes: bytes) -> None:
    app.dependency_overrides[get_pipeline] = _pipeline
    try:
        response = _post(TestClient(app), synthetic_image_bytes)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPT"


def test_real_stub_pipeline_requires_review(synthetic_image_bytes: bytes) -> None:
    with TestClient(app) as client:
        response = _post(client, synthetic_image_bytes)
        health = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "MANUAL_REVIEW"
    assert len(response.json()["stage_results"]) == 5
    reason_codes = [item["code"] for item in response.json()["reasons"]]
    assert reason_codes == ["STAGE_NOT_EVALUATED"]
    assert health.json()["status"] == "ok"
    assert len(health.json()["not_evaluated_stages"]) == 5


def test_health_is_not_ready_without_startup() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert set(response.json()) == {
        "status",
        "service_version",
        "model_versions",
        "not_evaluated_stages",
    }


def _reencode(image: bytes, format_name: str) -> bytes:
    with Image.open(BytesIO(image)) as source:
        output = BytesIO()
        source.save(output, format=format_name)
        return output.getvalue()


def _large_header_png(original: bytes) -> bytes:
    image = bytearray(original)
    image[16:24] = struct.pack(">II", 5000, 5000)
    image[29:33] = struct.pack(">I", zlib.crc32(image[12:29]))
    return bytes(image)


@pytest.mark.parametrize(
    ("image_case", "expected_status", "expected_code"),
    [
        ("oversized", 413, "FILE_TOO_LARGE"),
        ("unsupported", 422, "UNSUPPORTED_FORMAT"),
        ("corrupt", 422, "IMAGE_DECODE_FAILED"),
    ],
)
def test_upload_boundary_errors(
    image_case: str,
    expected_status: int,
    expected_code: str,
    synthetic_image_bytes: bytes,
) -> None:
    images = {
        "oversized": b"x" * (get_app_settings().max_file_bytes + 1),
        "unsupported": _reencode(synthetic_image_bytes, "GIF"),
        "corrupt": b"\x89PNG\r\n\x1a\ninvalid",
    }
    image = images[image_case]
    response = _post(TestClient(app), image)

    assert response.status_code == expected_status
    assert response.json() == {"code": expected_code}


def test_webp_is_rejected_by_default_configuration(synthetic_image_bytes: bytes) -> None:
    response = _post(TestClient(app), _reencode(synthetic_image_bytes, "WEBP"))

    assert "WEBP" not in get_app_settings().allowed_formats
    assert response.status_code == 422
    assert response.json() == {"code": "UNSUPPORTED_FORMAT"}


def test_webp_can_be_enabled_in_allowed_formats(synthetic_image_bytes: bytes) -> None:
    settings = get_app_settings()
    enabled = settings.model_copy(update={"allowed_formats": [*settings.allowed_formats, "WEBP"]})

    decoded = decode_bgr_image(_reencode(synthetic_image_bytes, "WEBP"), enabled)

    assert decoded.shape == (32, 48, 3)


def test_declared_pixel_limit_checked_before_decode(synthetic_image_bytes: bytes) -> None:
    response = _post(TestClient(app), _large_header_png(synthetic_image_bytes))

    assert response.status_code == 422
    assert response.json() == {"code": "IMAGE_TOO_LARGE"}


def test_stage_exception_returns_sanitized_503(synthetic_image_bytes: bytes) -> None:
    class BrokenStage:
        name = "detection"
        implemented = True

        def run(self, ctx: PipelineContext) -> StageResult:
            raise RuntimeError("private image detail")

    settings = load_pipeline_settings(Path(__file__).resolve().parents[1] / "configs/pipeline.yaml")
    app.dependency_overrides[get_pipeline] = lambda: EkycPipeline([BrokenStage()], settings)
    try:
        response = _post(TestClient(app), synthetic_image_bytes)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"code": "VERIFICATION_UNAVAILABLE"}
