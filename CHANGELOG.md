# Changelog

Format: [Keep a Changelog](https://keepachangelog.com). Versions follow milestones (M1 = 0.1, M2 = 0.2, …).

## [Unreleased]
### Changed
- Detector now serves the notebooks' ONNX exports (fixed or dynamic batch) with calibrated thresholds
- Server is torch-free: onnxruntime for detection, Chroma ONNX embeddings for RAG; Docker on Python 3.12
- PCB product maps to VisA `pcb1`; SOPs moved to `data/knowledge_base/`
- Progress tracker mirrors Tracker v2 IDs; results table built from `results/results_log.csv`
### Added
- Switchable language model: `LLM_PROVIDER` = gemini (free tier) | claude | ollama | none
- GitHub Codespaces setup (`.devcontainer/devcontainer.json`)
- `scripts/check_parity.py` (tracker 2.1 gate), `scripts/upload_weights.py` for the Drive layout
- `data/eval_labels.csv` template (tracker 5.1)
### Removed
- `training/train_patchcore.py` (the Colab notebooks are the training source)

## [0.1.0] — 2026-11-03
### Added
- Three-layer pipeline: PatchCore detector, Claude defect description, SOP-grounded report via RAG
- FastAPI service (`/health`, `/inspect`, `/history`, `/sops/reload`) and Streamlit dashboard
- Offline fallbacks: demo detector, keyword retrieval, rule-based report
- PatchCore training/export script for Colab; weight upload to the HF Hub
- CI (ruff + pytest) and auto-deploy to Hugging Face Spaces
- Sample SOPs: SOP-BTL-001 (bottles), SOP-PCB-001 (PCBs)
