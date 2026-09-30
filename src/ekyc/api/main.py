"""FastAPI entry point for eKYC verification."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse

from ekyc.api.deps import get_app_settings, get_pipeline
from ekyc.api.schemas import DecisionResponse, HealthResponse
from ekyc.common.config import AppSettings
from ekyc.common.image_io import ImageInputError, decode_bgr_image
from ekyc.common.types import PipelineContext
from ekyc.pipeline import EkycPipeline, StageExecutionError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize singleton configuration and stages once at application startup."""
    app.state.pipeline_ready = False
    get_app_settings()
    get_pipeline()
    app.state.pipeline_ready = True
    yield
    app.state.pipeline_ready = False


def create_app() -> FastAPI:
    """Create the application with replaceable dependencies for test isolation."""
    app = FastAPI(title="eKYC API", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(ImageInputError)
    async def image_error_handler(_request: object, exc: ImageInputError) -> JSONResponse:
        """Return only a stable boundary error code."""
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code})

    @app.exception_handler(StageExecutionError)
    async def stage_error_handler(_request: object, _exc: StageExecutionError) -> JSONResponse:
        """Hide internal stage details from the public response."""
        return JSONResponse(status_code=503, content={"code": "VERIFICATION_UNAVAILABLE"})

    @app.get("/health", response_model=HealthResponse)
    def health(
        request: Request,
        settings: AppSettings = Depends(get_app_settings),
    ) -> HealthResponse:
        """Return service state and configured model versions."""
        ready = getattr(request.app.state, "pipeline_ready", False)
        return HealthResponse(
            status="ok" if ready else "not_ready",
            service_version=settings.service.version,
            model_versions=settings.model_versions,
            not_evaluated_stages=get_pipeline().not_evaluated_stages if ready else [],
        )

    @app.post("/v1/verify", response_model=DecisionResponse)
    async def verify(
        id_front: UploadFile = File(...),
        selfie: UploadFile = File(...),
        pipeline: EkycPipeline = Depends(get_pipeline),
        settings: AppSettings = Depends(get_app_settings),
    ) -> DecisionResponse:
        """Decode both multipart images and run the injected eKYC pipeline."""
        id_content = await id_front.read(settings.max_file_bytes + 1)
        selfie_content = await selfie.read(settings.max_file_bytes + 1)
        context = PipelineContext(
            id_front=decode_bgr_image(id_content, settings),
            selfie=decode_bgr_image(selfie_content, settings),
        )
        decision = pipeline.verify(context)
        return DecisionResponse.from_domain(decision)

    return app


app = create_app()
