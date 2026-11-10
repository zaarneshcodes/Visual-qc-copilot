"""Central configuration. Every setting comes from environment variables (or a .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional; in Docker/HF Spaces env vars are injected directly
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent

SUPPORTED_PRODUCTS = ("bottle", "pcb")
# Product line shown in the UI -> dataset category used in the notebooks' file names
PRODUCT_CATEGORY = {"bottle": "bottle", "pcb": "pcb1"}


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # --- Language-model layer (VLM description + report) ---
    # auto | claude | gemini | ollama | none   (auto = first provider with a key, else none)
    llm_provider_setting: str = field(default_factory=lambda: _env("LLM_PROVIDER", "auto").lower())
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    claude_model: str = field(default_factory=lambda: _env("CLAUDE_MODEL", "claude-sonnet-5-5"))
    # Free tier: create a key at aistudio.google.com. Model names change; check AI Studio's list.
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-flash-latest"))
    # Local models via Ollama (ollama.com), e.g. `ollama pull qwen2.5vl:3b`
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _env("OLLAMA_MODEL", "qwen2.5vl:3b"))

    # --- Anomaly detection layer ---
    # Folder holding {model}_{category}.onnx and calibration_{model}_{category}.json
    models_dir: Path = field(default_factory=lambda: Path(_env("MODELS_DIR", str(ROOT_DIR / "models"))))
    # Optional: Hugging Face model repo to download those files from at startup
    hf_model_repo: str = field(default_factory=lambda: _env("HF_MODEL_REPO"))
    # Which trained model serves each product line ("patchcore" or "padim")
    model_bottle: str = field(default_factory=lambda: _env("MODEL_BOTTLE", "patchcore"))
    model_pcb: str = field(default_factory=lambda: _env("MODEL_PCB", "patchcore"))
    # "balanced" (Youden threshold) or "zero_false_alarm" from the calibration file
    threshold_policy: str = field(default_factory=lambda: _env("THRESHOLD_POLICY", "balanced"))
    # Used only when no calibration file exists (and by the demo detector)
    anomaly_threshold: float = field(default_factory=lambda: float(_env("ANOMALY_THRESHOLD", "0.5")))
    # "none": feed raw 0..1 pixels (Anomalib 2.x exports normalise inside the graph). "imagenet" otherwise.
    onnx_input_norm: str = field(default_factory=lambda: _env("ONNX_INPUT_NORM", "none"))
    # "auto" = ONNX model if present, else demo heuristic. "demo" forces the heuristic.
    detector_mode: str = field(default_factory=lambda: _env("DETECTOR_MODE", "auto"))

    # --- RAG layer ---
    sops_dir: Path = field(default_factory=lambda: Path(_env("SOPS_DIR", str(ROOT_DIR / "data" / "knowledge_base"))))
    # "chroma" (LangChain + Chroma, ONNX MiniLM embeddings, no torch) or "keyword" (no ML deps, used in CI)
    rag_backend: str = field(default_factory=lambda: _env("RAG_BACKEND", "chroma"))
    rag_top_k: int = field(default_factory=lambda: int(_env("RAG_TOP_K", "4")))

    # --- Service wiring ---
    api_url: str = field(default_factory=lambda: _env("API_URL", "http://localhost:8000"))
    max_upload_mb: int = field(default_factory=lambda: int(_env("MAX_UPLOAD_MB", "10")))

    def model_for(self, product: str) -> str:
        return self.model_bottle if product == "bottle" else self.model_pcb

    @property
    def llm_provider(self) -> str:
        choice = self.llm_provider_setting
        if choice == "auto":
            if self.anthropic_api_key:
                return "claude"
            if self.gemini_api_key:
                return "gemini"
            return "none"
        if choice == "claude" and not self.anthropic_api_key:
            return "none"
        if choice == "gemini" and not self.gemini_api_key:
            return "none"
        return choice if choice in ("claude", "gemini", "ollama") else "none"

    @property
    def has_llm(self) -> bool:
        return self.llm_provider != "none"

    @property
    def llm_label(self) -> str:
        """Shown in /health, the dashboard and each report's generated_by field."""
        return {
            "claude": f"claude:{self.claude_model}",
            "gemini": f"gemini:{self.gemini_model}",
            "ollama": f"ollama:{self.ollama_model}",
        }.get(self.llm_provider, "offline (no language model configured)")


settings = Settings()
