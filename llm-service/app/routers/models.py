"""Models list router for LLM Service

Exposes GET /v1/models endpoint listing available models.
"""

import logging
from fastapi import APIRouter, status, Depends
from app.models.completions import ModelListResponse, ModelInfo
from app.services.model_manager import ModelManager

logger = logging.getLogger(__name__)
router = APIRouter()


def get_model_manager_dependency():
    """Get model manager for dependency injection."""
    from app.main import get_model_manager
    return get_model_manager()


@router.get("/v1/models", response_model=ModelListResponse, tags=["models"])
async def list_models(model_manager: ModelManager = Depends(get_model_manager_dependency)) -> ModelListResponse:
    """
    List all available LLM models.

    OpenAI-compatible endpoint returning model information.

    Returns:
        ModelListResponse containing list of available models
    """
    try:

        # Build model list
        models = []

        # Standard model
        models.append(ModelInfo(
            id=model_manager.config.llm_model_standard,
            object="model",
            owned_by="meta",
            permission=[]
        ))

        # Long context model
        models.append(ModelInfo(
            id=model_manager.config.llm_model_longctx,
            object="model",
            owned_by="mistral",
            permission=[]
        ))

        # Multimodal model
        models.append(ModelInfo(
            id=model_manager.config.llm_model_multimodal,
            object="model",
            owned_by="google",
            permission=[]
        ))

        return ModelListResponse(
            object="list",
            data=models
        )

    except Exception as e:
        logger.error("Failed to list models", exc_info=True)
        raise
