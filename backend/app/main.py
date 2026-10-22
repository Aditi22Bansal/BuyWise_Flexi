from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router as api_router
from app.db.session import init_db
from app.services.workflow import reconcile_stuck_workflows

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BuyWise Multi-Agent Procurement Automation Platform",
)

# CORS — hardcoded to avoid pydantic-settings JSON parsing issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        reconcile_stuck_workflows()
    except Exception as e:
        # Don't crash on startup if DB is unavailable; endpoints will return errors
        print(f"Warning: DB initialization failed: {e}")


@app.get("/")
def root():
    return {"service": "BuyWise Backend", "version": settings.VERSION, "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "BuyWise Backend", "version": settings.VERSION}