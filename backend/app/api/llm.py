from fastapi import APIRouter

from app.llm.provider import get_llm_status

router = APIRouter(tags=["llm"])


@router.get("/llm/status")
def llm_status():
    return get_llm_status()
