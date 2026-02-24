"""FastAPI main application for LLM Service

Multi-model LLM inference service with OpenAI-compatible API.
"""

import logging
import structlog
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, REGISTRY
from fastapi.responses import Response

from app import __version__
from app.config import get_config
from app.services.model_manager import ModelManager
from app.services.generation import GenerationService
from app.services.guardrails import GuardrailsService
from app.services.prompt_templates import PromptTemplateService
from app.utils.langfuse_tracer import LangfuseTracer
from app.utils.metrics import MetricsCollector
from app.routers import health, models, completions

# Configure structured logging
def setup_logging(config):
    """Setup structured JSON logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO if config.app_env == "production" else logging.DEBUG)

    return root_logger


# Global service instances
_config: Optional[object] = None
_model_manager: Optional[ModelManager] = None
_generation_service: Optional[GenerationService] = None
_guardrails_service: Optional[GuardrailsService] = None
_prompt_templates: Optional[PromptTemplateService] = None
_tracer: Optional[LangfuseTracer] = None
_metrics: Optional[MetricsCollector] = None


def get_config_instance():
    """Get config singleton"""
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_model_manager() -> ModelManager:
    """Get model manager singleton"""
    global _model_manager
    if _model_manager is None:
        config = get_config_instance()
        _model_manager = ModelManager(config)
    return _model_manager


def get_generation_service() -> GenerationService:
    """Get generation service singleton"""
    global _generation_service
    if _generation_service is None:
        model_manager = get_model_manager()
        prompt_templates = get_prompt_templates()
        tracer = get_tracer()
        _generation_service = GenerationService(
            model_manager=model_manager,
            prompt_templates=prompt_templates,
            tracer=tracer
        )
    return _generation_service


def get_guardrails_service() -> GuardrailsService:
    """Get guardrails service singleton"""
    global _guardrails_service
    if _guardrails_service is None:
        _guardrails_service = GuardrailsService()
    return _guardrails_service


def get_prompt_templates() -> PromptTemplateService:
    """Get prompt templates singleton"""
    global _prompt_templates
    if _prompt_templates is None:
        _prompt_templates = PromptTemplateService()
    return _prompt_templates


def get_tracer() -> LangfuseTracer:
    """Get Langfuse tracer singleton"""
    global _tracer
    if _tracer is None:
        config = get_config_instance()
        _tracer = LangfuseTracer(config)
    return _tracer


def get_metrics() -> MetricsCollector:
    """Get metrics collector singleton"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler (startup and shutdown)"""
    config = get_config_instance()
    logger = logging.getLogger(__name__)

    # Startup
    try:
        logger.info(
            "LLM Service starting",
            extra={"version": __version__, "env": config.app_env}
        )

        # Initialize model manager
        model_manager = get_model_manager()
        if config.llm_load_on_startup:
            await model_manager.initialize()

        # Initialize metrics
        metrics = get_metrics()
        for model_key in ["standard", "longctx", "multimodal"]:
            metrics.record_model_loaded(
                model=model_key,
                is_loaded=model_manager.is_model_loaded(model_key)
            )

        logger.info("LLM Service startup complete")

    except Exception as e:
        logger.error("LLM Service startup failed", exc_info=True)
        raise

    yield

    # Shutdown
    try:
        logger.info("LLM Service shutting down")
        model_manager = get_model_manager()
        await model_manager.shutdown()
        logger.info("LLM Service shutdown complete")

    except Exception as e:
        logger.error("LLM Service shutdown failed", exc_info=True)


# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    config = get_config_instance()
    setup_logging(config)

    app = FastAPI(
        title="LLM Service",
        description="Multi-model LLM inference service with OpenAI-compatible API",
        version=__version__,
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)
    app.include_router(completions.router)

    # Metrics endpoint
    @app.get("/metrics", tags=["metrics"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(REGISTRY),
            media_type="text/plain"
        )

    # Root endpoint
    @app.get("/", tags=["info"])
    async def root():
        """Root endpoint with service information"""
        return {
            "service": "llm-service",
            "version": __version__,
            "status": "healthy"
        }

    # Error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler"""
        logger = logging.getLogger(__name__)
        logger.error("Unhandled exception", exc_info=exc)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred"
                }
            }
        )

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    config = get_config_instance()
    uvicorn.run(
        app,
        host=config.service_host,
        port=config.service_port,
        workers=1,
        log_level="info" if config.app_env == "production" else "debug"
    )
