---
title: Visual QC Copilot
emoji: 🔍
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Industrial defect detection with PatchCore, a VLM and SOP RAG
---

# Visual QC Copilot

[![CI](https://github.com/zaarneshcodes/visual-qc-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/zaarneshcodes/visual-qc-copilot/actions/workflows/ci.yml)

An industrial visual inspection assistant. It finds anomalies on a product image, describes the
defect in plain language, and writes a QC report that cites the factory's own SOPs.

**Live demo:** https://huggingface.co/spaces/Zaarneshcodes/visual-qc-copilot

## How it works

```
image ──► 1. PatchCore / PaDiM (ONNX) ──► score + heatmap, calibrated threshold
                │ flagged?
                ▼
          2. Vision-language model ──► defect type, location, description
             (Gemini free tier, Claude, or a local Ollama model — one setting)
                │
                ▼
          3. RAG over SOPs (LangChain + Chroma) ──► severity, disposition, actions, citations
                │
                ▼
          FastAPI  ◄──►  Streamlit dashboard
```

- **Layer 1, anomaly detection.** PatchCore and PaDiM (Anomalib 2.7) trained in Colab on defect-free images only
  (MVTec AD *bottle*, VisA *pcb1*), exported to ONNX and served with onnxruntime, so the server needs no torch.
  Decision thresholds are calibrated on one half of the test set and checked on the other, not fixed at 0.5.
- **Layer 2, VLM description.** Only flagged units go to the vision-language model, together with the heatmap and the
  region statistics, so the model describes what the detector found instead of guessing. The provider is switchable
  with `LLM_PROVIDER` (`gemini` free tier, `claude`, local `ollama`, or `none`) using the same prompts.
- **Layer 3, grounded report.** The description is used to retrieve SOP sections; the report must cite them and
  escalates when the SOPs do not cover the case.

Every layer has an offline fallback (demo detector, keyword retrieval, rule-based report), so the app and CI run
without weights or an API key. The dashboard always shows which backend produced each result.

## Results

All numbers come from [`results/results_log.csv`](results/results_log.csv) (seed 42, Anomalib 2.7.0, Colab T4).
Recall and false-alarm rate (FAR) are on the held-out evaluation half at the balanced threshold.
CPU latency is the ONNX model on Colab CPU, median per full-size image.

| Category | Model | Image AUROC | Pixel AUROC | Recall | FAR | CPU ms |
|----------|-------|-------------|-------------|--------|-----|--------|
| bottle | PatchCore | 1.000 | 0.986 | 1.00 | 0.00 | 1016 |
| bottle | PaDiM | 0.998 | 0.979 | 1.00 | 0.00 | 87 |
| pcb1 | PatchCore | 0.937 | 0.996 | 0.94 | 0.16 | 3874 |
| pcb1 | PaDiM | 0.793 | 0.982 | 0.68 | 0.12 | 121 |

Bottle is close to solved, and PaDiM gets there 12× faster. PCB is the open problem: PatchCore still raises
false alarms on about one good board in six at 94% recall.

## Quick start

No installs: on GitHub click **Code → Codespaces → Create codespace on main**; tools install themselves.
On your own machine:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: copy .env.example .env   — then add a free GEMINI_API_KEY

# terminal 1
uvicorn qc_copilot.api:app --reload --port 8000
# terminal 2
streamlit run dashboard/streamlit_app.py
```

Open http://localhost:8501. Without model files the app runs a clearly labelled demo detector. To serve your
trained models and semantic SOP search, follow Phase 4 of [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

## Repository map

| Path | What it is |
|------|------------|
| `qc_copilot/` | Backend package: ONNX detector, imaging, RAG, Claude calls, pipeline, FastAPI app |
| `dashboard/` | Streamlit UI |
| `notebooks/` | Colab training and benchmark notebooks (01 bottle, 03 PCB) |
| `results/` | `results_log.csv`, calibration files and run records copied from Drive |
| `data/knowledge_base/` | SOPs for RAG; `data/eval_labels.csv` holds hand labels for evaluation |
| `models/` | Downloaded `.onnx` files (git-ignored; hosted on the HF Hub) |
| `scripts/` | Upload models to the Hub; parity check against the notebook |
| `docs/` | Setup guide, architecture, tracker mirror, decision log, learning roadmap |
| `.github/workflows/` | CI (lint + tests) and auto-deploy to Hugging Face Spaces |

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Which detector, LLM and RAG backend are active |
| POST | `/inspect` | Multipart `file` + `product` (`bottle` or `pcb`) → full result |
| GET | `/history` | Last 50 results (in memory) |
| GET | `/history/{id}/report.md` | Markdown report |
| POST | `/sops/reload` | Re-index `data/knowledge_base/` after editing |

Interactive docs at http://localhost:8000/docs.

## Limitations

- History is in memory and resets on restart.
- The demo detector is a texture heuristic, not a model; use it only to exercise the pipeline.
- The sample SOPs are illustrative, not from a real plant.
- Bottle has only 20 normal test images, so its recall and FAR are coarse.
- Gemini's free tier has small daily limits; when they run out, reports fall back to rule-based output (labelled).

## License

MIT
