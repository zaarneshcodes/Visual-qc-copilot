"""Layer 2 (VLM defect description) and Layer 3b (SOP-grounded QC report).

Both layers degrade gracefully: with no language model configured, or if a call fails (e.g. a free-tier quota), they return
rule-based output marked with "generated_by": "fallback" so nothing downstream breaks.
"""
from __future__ import annotations

import json
import logging

from . import llm
from .config import settings
from .rag import Chunk

log = logging.getLogger(__name__)

DESCRIBE_SYSTEM = """You are a visual quality-control inspector on a factory line.
You receive (1) a product photo and (2) the same photo with an anomaly heatmap overlay
(red/yellow = most anomalous) plus numeric detector output.
Describe only what is visible. If the heatmap highlights something that looks normal, say so.
Reply with ONLY a JSON object, no prose, with keys:
  "defect_present": boolean,
  "defect_type": short label (e.g. "crack", "contamination", "broken_large", "missing_component", "solder_bridge", "none"),
  "location": short phrase,
  "visual_description": 1-3 sentences,
  "confidence": "low" | "medium" | "high",
  "agrees_with_detector": boolean"""

REPORT_SYSTEM = """You are a QC engineer writing an inspection report.
Use ONLY the SOP excerpts provided to decide severity and disposition, and cite the SOP id
and section for each rule you apply. If the SOPs do not cover the case, set disposition to
"escalate" and say which information is missing. Never invent SOP clauses.
Reply with ONLY a JSON object with keys:
  "verdict": "PASS" | "FAIL" | "REVIEW",
  "severity": "none" | "minor" | "major" | "critical",
  "disposition": "accept" | "rework" | "scrap" | "escalate",
  "summary": 1-2 sentences,
  "actions": list of short imperative steps,
  "sop_citations": list of {"sop": id, "section": heading, "rule": short paraphrase}"""


def describe_defect(product: str, b64_original: str, b64_overlay: str, detection: dict) -> dict:
    if settings.has_llm:
        try:
            content = [
                llm.image_block(b64_original),
                llm.image_block(b64_overlay),
                llm.text_block(f"Product: {product}\nDetector output: {json.dumps(detection)}\nDescribe the defect."),
            ]
            out = llm.ask_json(DESCRIBE_SYSTEM, content, max_tokens=600)
            out["generated_by"] = settings.llm_label
            return out
        except Exception as exc:
            log.error("VLM description failed: %s", exc)
    return fallback_description(detection)


def fallback_description(detection: dict) -> dict:
    flagged = detection["is_defective"]
    region = detection.get("region", {})
    return {
        "defect_present": flagged,
        "defect_type": "unclassified_anomaly" if flagged else "none",
        "location": region.get("location", "unknown") if flagged else "n/a",
        "visual_description": (
            f"Detector flagged an anomalous region ({region.get('area_fraction', 0):.1%} of the image) "
            f"near the {region.get('location', 'unknown')} area. Configure a language model for a visual description."
            if flagged
            else "No anomaly above threshold."
        ),
        "confidence": "low",
        "agrees_with_detector": True,
        "generated_by": "fallback",
    }


def build_query(product: str, description: dict) -> str:
    return (
        f"{product} {description.get('defect_type', '')} {description.get('location', '')} "
        f"{description.get('visual_description', '')} severity disposition acceptance criteria"
    )


def _format_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{c.source} — {c.section}]\n{c.text}" for c in chunks) or "(no SOP excerpts found)"


def write_report(product: str, detection: dict, description: dict, chunks: list[Chunk]) -> dict:
    if settings.has_llm:
        try:
            content = [
                llm.text_block(
                    f"Product: {product}\nDetector: {json.dumps(detection)}\n"
                    f"Inspector description: {json.dumps(description)}\n\n"
                    f"SOP excerpts:\n{_format_context(chunks)}"
                )
            ]
            out = enforce_consistency(llm.ask_json(REPORT_SYSTEM, content, max_tokens=1200))
            out["generated_by"] = settings.llm_label
            return out
        except Exception as exc:
            log.error("Report generation failed: %s", exc)
    return _fallback_report(detection, chunks)


# Which dispositions each verdict allows. Small models sometimes contradict themselves
# (e.g. FAIL + accept); a QC system must never ship that, so the code checks it.
ALLOWED_DISPOSITIONS = {
    "PASS": {"accept"},
    "FAIL": {"rework", "scrap", "escalate"},
    "REVIEW": {"escalate"},
}


def enforce_consistency(report: dict) -> dict:
    verdict = str(report.get("verdict", "")).upper()
    disposition = str(report.get("disposition", "")).lower()
    report["verdict"], report["disposition"] = verdict, disposition
    if disposition not in ALLOWED_DISPOSITIONS.get(verdict, set()):
        report["consistency_note"] = (
            f"Model returned verdict {verdict or '?'} with disposition {disposition or '?'}, "
            "which contradict each other; routed to human review."
        )
        report["verdict"], report["disposition"] = "REVIEW", "escalate"
    return report


def pass_report() -> dict:
    return {
        "verdict": "PASS",
        "severity": "none",
        "disposition": "accept",
        "summary": "Anomaly score is below the line threshold; no defect flagged.",
        "actions": [],
        "sop_citations": [],
        "generated_by": "rule (below threshold)",
    }


def _fallback_report(detection: dict, chunks: list[Chunk]) -> dict:
    if not detection["is_defective"]:
        return pass_report()
    return {
        "verdict": "REVIEW",
        "severity": "unknown",
        "disposition": "escalate",
        "summary": (
            "Anomaly detected; route the unit to manual inspection. "
            "Severity was not assessed because the language-model layer is offline."
        ),
        "actions": ["Hold the unit", "Inspect it manually against the SOP sections listed below"],
        "sop_citations": [{"sop": c.source, "section": c.section, "rule": "retrieved for reference"} for c in chunks],
        "generated_by": "fallback",
    }