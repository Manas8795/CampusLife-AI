import os
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.observability import configure_logging, CorrelationIDMiddleware

# Configure structured JSON logging at startup
configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("campuslife.main")

# Import all models to ensure SQLAlchemy registers them in Base.metadata
import backend.app.core.models
import backend.app.study.models
import backend.app.health.models
import backend.app.expenses.models
import backend.app.travel.models
import backend.app.intelligence.models
import backend.app.voice.models

# Routers
from backend.app.core.router import router as core_router
from backend.app.study.router import router as study_router
from backend.app.health.router import router as health_router
from backend.app.expenses.router import router as expenses_router
from backend.app.travel.router import router as travel_router
from backend.app.intelligence.router import router as intelligence_router
from backend.app.voice.router import router as voice_router
from backend.app.infra.router import router as infra_router

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CampusLife AI — Unified Student Co-Pilot Backend (Modules 1 to 8 Active & Deployed)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware — injects X-Correlation-ID into every request log
app.add_middleware(CorrelationIDMiddleware)

# Mount Routers under /api
app.include_router(core_router, prefix="/api")
app.include_router(study_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
app.include_router(travel_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(infra_router, prefix="/api")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def serve_static_page(filename: str):
    file_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"<h1>CampusLife AI</h1><p>Page {filename} not found.</p>"

@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    return serve_static_page("index.html")

@app.get("/study", response_class=HTMLResponse)
def study_page():
    return serve_static_page("study.html")

@app.get("/health", response_class=HTMLResponse)
def health_page():
    return serve_static_page("health.html")

@app.get("/expenses", response_class=HTMLResponse)
def expenses_page():
    return serve_static_page("expenses.html")

@app.get("/travel", response_class=HTMLResponse)
def travel_page():
    return serve_static_page("travel.html")

@app.get("/intelligence", response_class=HTMLResponse)
def intelligence_page():
    return serve_static_page("intelligence.html")

@app.get("/voice", response_class=HTMLResponse)
def voice_page():
    return serve_static_page("voice.html")

@app.get("/call", response_class=HTMLResponse)
@app.get("/mobile-call", response_class=HTMLResponse)
def mobile_call_page():
    return serve_static_page("mobile_call.html")

@app.get("/infra", response_class=HTMLResponse)
def infra_page():
    return serve_static_page("infra.html")

@app.get("/api/status")
def status_json():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "active_modules": [
            "Module 1: Platform Core & User Management",
            "Module 2: To-Do & Study Planner",
            "Module 3: Health & Wellness",
            "Module 4: Expense & Financial Manager",
            "Module 5: Travel & Trip Planner",
            "Module 6: Student Intelligence Engine",
            "Module 7: AI Voice Assistant & Calling System",
            "Module 8: AI/ML Infrastructure & Deployment"
        ],
        "docs_url": "/docs"
    }

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def on_startup():
    import asyncio
    from backend.app.voice.deadline_watcher import deadline_watcher
    asyncio.create_task(deadline_watcher.start())

