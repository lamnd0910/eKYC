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
    assert pipeline_settings.face_match.below_action == "REJECT"
    assert pipeline_settings.ocr_confidence.below_action == "MANUAL_REVIEW"
    assert pipeline_settings.required_stages == ["detection", "quality", "antispoof", "ocr", "face"]
    assert app_settings.max_pixels > 0


def test_uncertainty_range_requires_ordered_thresholds() -> None:
    with pytest.raises(ValueError, match="manual_review_low"):
        PipelineSettings.model_validate(
            {
                "face_match": {
                    "manual_review_low": 0.8,
                    "manual_review_high": 0.7,
                    "below_action": "REJECT",
                },
                "ocr_confidence": {
                    "manual_review_low": 0.7,
                    "manual_review_high": 0.9,
                    "below_action": "MANUAL_REVIEW",
                },
                "required_stages": ["detection", "quality", "antispoof", "ocr", "face"],
            }
        )


@pytest.mark.parametrize("stage_name", ("face_match", "ocr_confidence"))
def test_missing_below_action_is_invalid(stage_name: str) -> None:
    settings = load_pipeline_settings(Path(__file__).resolve().parents[1] / "configs/pipeline.yaml")
    config = settings.model_dump()
    del config[stage_name]["below_action"]

    with pytest.raises(ValueError, match="below_action"):
        PipelineSettings.model_validate(config)


@pytest.mark.parametrize("stage_name", ("face_match", "ocr_confidence"))
def test_unknown_below_action_is_invalid(stage_name: str) -> None:
    settings = load_pipeline_settings(Path(__file__).resolve().parents[1] / "configs/pipeline.yaml")
    config = settings.model_dump()
    config[stage_name]["below_action"] = "ACCEPT"

    with pytest.raises(ValueError, match="below_action"):
        PipelineSettings.model_validate(config)
