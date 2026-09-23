"""YAML-backed, typed application configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class UncertaintyRange(BaseModel):
    """Exclusive lower/inclusive upper score range requiring human review."""

    model_config = ConfigDict(extra="forbid")

    manual_review_low: float = Field(ge=0.0, le=1.0)
    manual_review_high: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_order(self) -> UncertaintyRange:
        if self.manual_review_low >= self.manual_review_high:
            raise ValueError("manual_review_low must be less than manual_review_high")
        return self

    def contains(self, score: float) -> bool:
        """Return whether score is within the manual-review interval."""
        return self.manual_review_low <= score < self.manual_review_high


class PipelineSettings(BaseModel):
    """Decision thresholds loaded from ``pipeline.yaml``."""

    model_config = ConfigDict(extra="forbid")

    face_match: UncertaintyRange
    ocr_confidence: UncertaintyRange


class ServiceSettings(BaseModel):
    """Public service identity."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str


class AppSettings(BaseModel):
    """Base application settings loaded from ``base.yaml``."""

    model_config = ConfigDict(extra="forbid")

    service: ServiceSettings
    model_versions: dict[str, str]


def load_yaml(path: Path) -> dict[str, Any]:
    """Read one mapping document from YAML and reject empty/non-mapping input."""
    with path.open(encoding="utf-8") as config_file:
        value = yaml.safe_load(config_file)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration at {path} must contain a YAML mapping")
    return value


def load_pipeline_settings(path: Path) -> PipelineSettings:
    """Load and validate decision threshold configuration."""
    return PipelineSettings.model_validate(load_yaml(path))


def load_app_settings(path: Path) -> AppSettings:
    """Load and validate base application configuration."""
    return AppSettings.model_validate(load_yaml(path))
