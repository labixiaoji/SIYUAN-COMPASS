from fastapi import APIRouter

from app.core.config import get_settings
from app.llm.deepseek import is_deepseek_configured

router = APIRouter(tags=["llm"])


@router.get("/llm/status")
def llm_status():
    settings = get_settings()
    return {
        "configured": is_deepseek_configured(),
        "model": settings.deepseek_model,
        "baseUrl": settings.deepseek_base_url,
    }
