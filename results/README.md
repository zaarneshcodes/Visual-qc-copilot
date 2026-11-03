# results/

Copied from `Drive/Visual QC Copilot/results/` so every number in the README traces to a file in git
(tracker 8.1). Copy these after each notebook run:

- `results_log.csv` — one row per run (source of the README results table)
- `calibration_{model}_{category}.json` — thresholds; the API reads these if `MODELS_DIR` has none
- `runs/run_*.json` — full run records, including the ONNX signature

The `.onnx` files themselves go to the Hugging Face Hub, not here.
