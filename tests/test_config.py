from pathlib import Path

import pytest

from ekyc.common.config import PipelineSettings, load_app_settings, load_pipeline_settings


def test_load_project_yaml_configuration() -> None:
    root = Path(__file__).resolve().parents[1]
    app_settings = load_app_settings(root / "configs" / "base.yaml")
    pipeline_settings = load_pipeline_settings(root / "configs" / "pipeline.yaml")

    assert app_settings.service.name == "ekyc"
    assert pipeline_settings.face_match.contains(0.60)
    assert not pipeline_settings.face_match.contains(0.80)


def test_uncertainty_range_requires_ordered_thresholds() -> None:
    with pytest.raises(ValueError, match="manual_review_low"):
        PipelineSettings.model_validate(
            {
                "face_match": {"manual_review_low": 0.8, "manual_review_high": 0.7},
                "ocr_confidence": {"manual_review_low": 0.7, "manual_review_high": 0.9},
            }
        )
