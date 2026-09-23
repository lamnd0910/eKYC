"""Application dependencies, kept replaceable for tests."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from ekyc.antispoof import AntiSpoofStage
from ekyc.common.config import AppSettings, load_app_settings, load_pipeline_settings
from ekyc.detection import DocumentDetectionStage
from ekyc.face import FaceMatchingStage
from ekyc.ocr import OcrStage
from ekyc.pipeline import EkycPipeline
from ekyc.quality import ImageQualityStage


def _config_dir() -> Path:
    """Resolve configuration directory, allowing container configuration."""
    configured_dir = os.getenv("E_KYC_CONFIG_DIR")
    if configured_dir:
        return Path(configured_dir)
    return Path(__file__).resolve().parents[3] / "configs"


@lru_cache
def get_app_settings() -> AppSettings:
    """Load base settings once during application lifetime."""
    return load_app_settings(_config_dir() / "base.yaml")


@lru_cache
def get_pipeline() -> EkycPipeline:
    """Construct singleton default stages and their shared decision policy."""
    settings = load_pipeline_settings(_config_dir() / "pipeline.yaml")
    return EkycPipeline(
        stages=(
            DocumentDetectionStage(),
            ImageQualityStage(),
            AntiSpoofStage(),
            OcrStage(),
            FaceMatchingStage(),
        ),
        settings=settings,
    )
