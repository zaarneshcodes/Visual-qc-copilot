# Progress tracker

Mirrors the Google Sheet **Visual QC Copilot – Tracker v2 (roadmap)**, same IDs. The sheet stays the
planning view; this file is the record in git. Status below is taken from `results/results_log.csv`
and the files in Drive as of 2026-11-03 — update the sheet to match.

Repo paths replace the sheet's planned `code/...` paths: a Python package named `code` would shadow
Python's built-in `code` module, so the backend lives in `qc_copilot/`.

| ID | Task | Repo / Drive file | Status | Evidence |
|----|------|-------------------|--------|----------|
| 0.1 | One project folder: Drive/Visual QC Copilot | Drive | Check | Delete `Visual_QC_Copilot` (underscores) if it still exists |
| 0.2 | Archive old 01 notebooks | `notebooks/archive/` | Not done | Drive still has `01_Training_PatchCore`, `_v2`, `_v2_1`, `_v2_2` |
| 0.3 | v2 notebook in project root | Drive | Done | |
| 1.1 | PatchCore on MVTec bottle | `notebooks/01_Training_PatchCore.ipynb` | Done | image AUROC 1.000, pixel 0.986, ONNX ok (2026-10-30 19:53) |
| 1.2 | PaDiM baseline on bottle | same | Done | image AUROC 0.998, pixel 0.979, 87 ms CPU (2026-11-02 15:11) |
| 1.3 | Calibrated threshold saved | `results/calibration_*.json` | Done | PatchCore bottle balanced threshold 0.4013, eval-half recall 1.0, FAR 0.0 |
| 2.1 | Inference from the measured ONNX signature | `qc_copilot/detector.py` | In review | Code handles batch 2 and dynamic batch, reads calibration. Gate: `scripts/check_parity.py` matches the notebook's 16 decisions |
| 2.2 | Benchmark exported model on CPU | run JSONs | Done | PatchCore bottle 1016 ms, pcb1 3874 ms, PaDiM pcb1 120.5 ms median (Colab CPU) |
| 3.1 | PCB benchmark (VisA pcb1) | `notebooks/03_PCB_Benchmark.ipynb` | Done | PatchCore 0.937 / 0.996, recall 0.94 at FAR 0.16; PaDiM 0.793 / 0.982 |
| 4.1 | PatchCore vs PaDiM vs supervised few-label baseline | `notebooks/04_Method_Comparison.ipynb` | Unblocked | Two of three methods logged; supervised baseline missing |
| 5.1 | Label 50 test images (defect type + SOP id) | `data/eval_labels.csv` | Not started | Header template committed |
| 5.2 | Score VLM description against labels | `scripts/` + 02 notebook Part B | Blocked by 5.1 | |
| 5.3 | Score RAG retrieval (top-1 / top-3) | `data/knowledge_base/` | Blocked by 5.1 | |
| 6.1 | FastAPI + Streamlit locally | `qc_copilot/api.py`, `dashboard/streamlit_app.py` | Built, not run | Gate: Setup guide Checkpoint 1b with real models (Checkpoint 4b) |
| 7.1 | Robustness to brightness / blur / rotation | `notebooks/05_Robustness.ipynb` | Not started | |
| 8.1 | README with figures, results table, demo video | `README.md`, `docs/figures/` | In progress | Results table filled from `results/results_log.csv` |
| 9.1 | Live demo on Hugging Face Spaces | `Dockerfile`, `.github/workflows/deploy-hf.yml` | Not started | Gate: Setup guide Checkpoint 5 |

## Log
| Date | What happened |
|------|---------------|
| 2026-11-03 | Repo realigned to the notebooks: ONNX serving, calibrated thresholds, VisA pcb1, tracker IDs |
| 2026-11-02 | PaDiM bottle, PatchCore + PaDiM pcb1 trained, exported and logged |
| 2026-10-30 | PatchCore bottle trained, calibrated, ONNX export verified |
