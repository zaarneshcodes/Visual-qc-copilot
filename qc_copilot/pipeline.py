"""Orchestrates the three layers: detect -> describe (VLM) -> retrieve SOPs -> report."""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

from . import copilot, imaging, rag
from .config import settings
from .detector import get_detector


def inspect(image_bytes: bytes, product: str, include_images: bool = True) -> dict:
    timings: dict[str, int] = {}

    def tick(name: str, start: float) -> float:
        now = time.perf_counter()
        timings[name] = round((now - start) * 1000)
        return now

    t = time.perf_counter()
    full = imaging.load_image(image_bytes)
    image = imaging.display_copy(full)

    # Layer 1 — anomaly detection on the full-size image
    det = get_detector(product).predict(full)
    region = imaging.defect_region_stats(det.anomaly_map)
    detection = {
        "score": round(det.score, 4),
        "threshold": round(det.threshold, 4),
        "threshold_policy": settings.threshold_policy,
        "is_defective": det.is_defective,
        "backend": det.backend,
        "region": region,
    }
    t = tick("detect_ms", t)

    overlay = imaging.overlay(image, det.anomaly_map)
    b64_original = imaging.to_base64_png(image)
    b64_overlay = imaging.to_base64_png(overlay)

    # Layer 2 — VLM description (skipped for clear passes to save API cost and latency)
    if det.is_defective:
        description = copilot.describe_defect(product, b64_original, b64_overlay, detection)
    else:
        description = copilot.fallback_description(detection)
        description["generated_by"] = "skipped (below threshold)"
    t = tick("describe_ms", t)

    # Layer 3 — retrieve SOPs and write the grounded report (LLM only for flagged units)
    chunks = rag.retrieve(copilot.build_query(product, description), product=product)
    if det.is_defective:
        report = copilot.write_report(product, detection, description, chunks)
    else:
        report = copilot.pass_report()
    tick("report_ms", t)

    result = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "product": product,
        "detection": detection,
        "description": description,
        "report": report,
        "retrieved_sops": [{"source": c.source, "section": c.section, "excerpt": c.text[:400]} for c in chunks],
        "timings_ms": timings,
    }
    if include_images:
        result["images"] = {
            "overlay_png_b64": b64_overlay,
            "heatmap_png_b64": imaging.to_base64_png(imaging.heatmap_image(det.anomaly_map, image.size)),
        }
    return result


def report_markdown(result: dict) -> str:
    """Human-readable report for download from the dashboard."""
    d, desc, r = result["detection"], result["description"], result["report"]
    lines = [
        f"# QC inspection report {result['id']}",
        "",
        f"- Product: {result['product']}",
        f"- Time (UTC): {result['timestamp']}",
        f"- Verdict: **{r.get('verdict')}** — severity {r.get('severity')}, disposition {r.get('disposition')}",
        f"- Anomaly score: {d['score']} (threshold {d['threshold']}, detector: {d['backend']})",
        "",
        "## Observation",
        desc.get("visual_description", ""),
        "",
        "## Summary",
        r.get("summary", ""),
        "",
        "## Actions",
        *[f"1. {a}" for a in r.get("actions", [])],
        "",
        "## SOP references",
        *[f"- {c.get('sop')} / {c.get('section')}: {c.get('rule')}" for c in r.get("sop_citations", [])],
        "",
        f"_Description by {desc.get('generated_by')}; report by {r.get('generated_by')}._",
    ]
    return "\n".join(lines)
