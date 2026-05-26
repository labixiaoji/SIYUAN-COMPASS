from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.assessments import router as assessments_router
from app.api.feedback import router as feedback_router
from app.api.llm import router as llm_router
from app.api.reports import router as reports_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Siyuan Compass API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(assessments_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
