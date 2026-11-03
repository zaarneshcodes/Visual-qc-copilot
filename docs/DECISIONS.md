# Decision log

One line per decision: what, why, and what was given up. Newest first.

| Date | Decision | Why | Trade-off |
|------|----------|-----|-----------|
| 2026-11-03 | Language model switchable: Gemini free tier (default when its key is set), Claude, Ollama, none | Zero-cost demo; providers can be compared on the same labels (tracker 5.2) | Free-tier daily limits are small and change; free-tier inputs may be used by Google, so only public images |
| 2026-11-03 | Gemini and Ollama via their OpenAI-compatible endpoints with plain `requests` | One code path, no extra SDKs | Provider-specific features (e.g. Gemini JSON mode) unused; JSON is parsed from text |
| 2026-11-03 | GitHub Codespaces config in `.devcontainer/` | Zero-install workspace in the browser, free monthly quota | Quota runs out if codespaces are left running |
| 2026-11-03 | Serve ONNX exports with onnxruntime, not Anomalib in the server | Notebooks already export and verify ONNX; server drops torch and anomalib, image builds in minutes | Retraining still needs Colab; preprocessing must match the export (checked by `scripts/check_parity.py`) |
| 2026-11-03 | Feed raw 0..1 full-size RGB to the ONNX model | Anomalib 2.x bakes resize + normalisation into the export; notebook check fed full-size images | If an export ever lacks normalisation, set `ONNX_INPUT_NORM=imagenet` |
| 2026-11-03 | Threshold from `calibration_{model}_{category}.json`, balanced policy by default | Calibrated on one half of test, checked on the other; replaces hard-coded 0.5 | Coarse on bottle (20 normal test images) |
| 2026-11-03 | PCB domain is VisA pcb1, UI product "pcb" maps to category "pcb1" | Matches notebook 03 and its file names | More PCB categories (pcb2–4) need a mapping entry each |
| 2026-11-03 | PatchCore default for both lines; PaDiM switchable per line | PatchCore is more accurate on pcb1 (0.937 vs 0.793) | pcb1 PatchCore ~3.9 s/image on CPU vs PaDiM ~0.12 s |
| 2026-11-03 | Backend package `qc_copilot/`, not `code/` | `code` is a Python standard-library module name | Tracker sheet paths updated to match |
| 2026-11-03 | RAG embeddings via Chroma's ONNX MiniLM | Keeps LangChain + Chroma without pulling torch through sentence-transformers | Fixed embedding model unless changed in `rag.py` |
| 2026-11-03 | Deploy as one Docker container on Hugging Face Spaces | Free, runs FastAPI + Streamlit together, auto-deploys from GitHub | Cold starts after inactivity; CPU only |
| 2026-11-03 | Models on the HF Hub, not in git | Files up to 177 MB; GitHub and Spaces reject large binaries | One upload step after training |
| 2026-11-03 | Call the VLM only for flagged units, with heatmap + region stats | Cuts API cost; grounds the description in what the detector found | Passing units get no language description |
| 2026-11-03 | Offline fallback for every layer | CI runs without models or keys; demo never hard-fails | Fallback output must be labelled (done in UI and JSON) |
