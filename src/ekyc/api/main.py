"""FastAPI entry point for eKYC verification."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status

from ekyc.api.deps import get_app_settings, get_pipeline
from ekyc.api.schemas import DecisionResponse, HealthResponse
from ekyc.common.config import AppSettings
from ekyc.common.image_io import decode_bgr_image
from ekyc.common.types import PipelineContext
from ekyc.pipeline import EkycPipeline


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize singleton configuration and stages once at application startup."""
    get_app_settings()
    get_pipeline()
    yield


def create_app() -> FastAPI:
    """Create the application with replaceable dependencies for test isolation."""
    app = FastAPI(title="eKYC API", version="0.1.0", lifespan=lifespan)

    @app.get("/health", response_model=HealthResponse)
    def health(settings: AppSettings = Depends(get_app_settings)) -> HealthResponse:
        """Return service state and configured model versions."""
        return HealthResponse(
            status="ok",
            service_version=settings.service.version,
            model_versions=settings.model_versions,
        )

    @app.post("/v1/verify", response_model=DecisionResponse)
    async def verify(
        id_front: UploadFile = File(...),
        selfie: UploadFile = File(...),
        pipeline: EkycPipeline = Depends(get_pipeline),
    ) -> DecisionResponse:
        """Decode both multipart images and run the injected eKYC pipeline."""
        try:
            context = PipelineContext(
                id_front=decode_bgr_image(await id_front.read()),
                selfie=decode_bgr_image(await selfie.read()),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc

        try:
            decision = pipeline.verify(context)
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Verification models are not installed yet",
            ) from exc
        return DecisionResponse.from_domain(decision)

    return app


app = create_app()
