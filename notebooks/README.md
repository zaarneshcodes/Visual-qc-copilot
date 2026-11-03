# Notebooks

Training and evaluation run in Google Colab from `Drive/Visual QC Copilot/`. Commit each notebook here
so the training code is versioned next to the serving code.

| Notebook | Tracker | Produces (in Drive `results/`) |
|----------|---------|-------------------------------|
| `01_Training_PatchCore.ipynb` (your latest `_v2_2`) | 1.1–1.3, 2.2 | `exported_models/{model}_bottle.onnx`, `calibration_*.json`, `runs/*.json`, `results_log.csv` row |
| `03_PCB_Benchmark.ipynb` | 3.1 | same, for `pcb1` |
| `02_Deployment_and_VLM_RAG_Demo.ipynb` | 2.2, 5.2 | superseded for serving by `qc_copilot/`; keep Part B for VLM scoring |

## Committing a notebook

1. In Colab: **Edit → Clear all outputs**, then **File → Download → Download .ipynb**.
   Outputs (images, logs) make the file tens of MB; the figures you want go to `docs/figures/` instead.
2. Rename to the name in the table and put it in this folder. Older versions go to `notebooks/archive/` (tracker 0.2).
3. Commit on a branch as described in the setup guide, Phase 3.

## After every training run

Copy these from Drive into the repo so the README numbers trace to git (tracker 8.1):
`results/results_log.csv`, `results/calibration_*.json`, `results/runs/*.json`.

## Publishing models for the app (once per new model)

Add this as the last cell of notebook 01 or 03:

```python
!pip -q install huggingface_hub
!git clone -q https://github.com/zaarneshcodes/visual-qc-copilot.git /content/vqc
from huggingface_hub import login
login()   # paste a WRITE token
!python /content/vqc/scripts/upload_weights.py --repo Zaarneshcodes/visual-qc-weights \
    --project "/content/drive/MyDrive/Visual QC Copilot"
```
