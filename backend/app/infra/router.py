import platform
import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.app.core.router import get_current_user_id
from backend.app.infra.llm_client import llm_client
from backend.app.infra.ml_serving import ModelRegistry
from backend.app.infra.ocr_engine import OCREngine
from backend.app.infra.rag_memory import rag_memory

router = APIRouter(prefix="/infra", tags=["AI/ML Infrastructure & Deployment"])

class LLMGenerateRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.7

class OCRTestRequest(BaseModel):
    receipt_text: str

class MemoryStoreRequest(BaseModel):
    category: str
    content: str
    importance: Optional[float] = 1.0

@router.get("/models")
def get_model_registry():
    """Lists all active ML models and their serving metadata."""
    return {
        "status": "SERVING",
        "total_models": len(ModelRegistry.MODELS_METADATA),
        "models": ModelRegistry.get_all_models()
    }

@router.post("/llm/generate")
def generate_llm(req: LLMGenerateRequest):
    """Executes prompt through the shared LLM Client."""
    output = llm_client.generate(req.prompt, temperature=req.temperature)
    return {
        "provider": llm_client.provider,
        "prompt": req.prompt,
        "output": output
    }

@router.post("/ocr/extract")
def run_ocr(req: OCRTestRequest):
    """Executes OCR receipt parsing pipeline."""
    return OCREngine.extract_text_from_receipt(req.receipt_text)

@router.get("/memory")
def get_semantic_memory(
    query: str = Query("exam and sleep", description="Search query for memory context"),
    user_id: int = Depends(get_current_user_id)
):
    """Retrieves relevant semantic RAG context from student history."""
    return {
        "user_id": user_id,
        "query": query,
        "contexts": rag_memory.retrieve_relevant_context(user_id, query)
    }

@router.get("/system/health")
def system_health():
    """Infrastructure and deployment health diagnostics."""
    return {
        "status": "HEALTHY",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "database": "SQLite / PostgreSQL Compatible",
        "shared_llm_status": "READY",
        "ml_serving_status": "SERVING",
        "active_modules": 8
    }
