"""FastAPI service. Run locally with:  uvicorn qc_copilot.api:app --reload --port 8000"""
from __future__ import annotations

import logging
from collections import deque

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from PIL import UnidentifiedImageError

from . import __version__, pipeline, rag
from .config import SUPPORTED_PRODUCTS, settings
from .detector import detector_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Visual QC Copilot API",
    version=__version__,
    description="Anomaly detection + VLM description + SOP-grounded QC reports.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Last 50 results kept in memory (a real deployment would write these to a database).
HISTORY: deque[dict] = deque(maxlen=50)


@app.get("/health")
def health() -> dict:
    retriever = rag.get_retriever()
    return {
        "status": "ok",
        "version": __version__,
        "detectors": detector_status(),
        "llm": settings.llm_label,
        "rag_backend": getattr(retriever, "backend", "unknown"),
        "sop_chunks": len(retriever.chunks) if hasattr(retriever, "chunks") else None,
    }


@app.get("/products")
def products() -> list[str]:
    return list(SUPPORTED_PRODUCTS)


@app.post("/inspect")
async def inspect(
    file: UploadFile = File(..., description="PNG or JPEG image of one unit"),
    product: str = Form("bottle"),
    include_images: bool = Form(True),
) -> dict:
    if product not in SUPPORTED_PRODUCTS:
        raise HTTPException(422, f"product must be one of {list(SUPPORTED_PRODUCTS)}")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File larger than {settings.max_upload_mb} MB")
    try:
        result = pipeline.inspect(data, product, include_images=include_images)
    except UnidentifiedImageError:
        raise HTTPException(400, "File is not a readable image (use PNG or JPEG)") from None
    HISTORY.appendleft({k: v for k, v in result.items() if k != "images"})
    return result


@app.get("/history")
def history(limit: int = 20) -> list[dict]:
    return list(HISTORY)[:limit]


@app.get("/history/{result_id}/report.md", response_class=PlainTextResponse)
def report_md(result_id: str) -> str:
    for item in HISTORY:
        if item["id"] == result_id:
            return pipeline.report_markdown(item)
    raise HTTPException(404, "Result not found (history is in-memory and resets on restart)")


@app.post("/sops/reload")
def reload_sops() -> dict:
    retriever = rag.get_retriever(rebuild=True)
    return {"rag_backend": retriever.backend, "sop_chunks": len(getattr(retriever, "chunks", []))}
