"""Upload exported ONNX models + calibration files from your Drive project folder to the HF Hub.

Run in Colab after mounting Drive (see notebooks/README.md), or locally:
    python scripts/upload_weights.py --repo <hf-username>/visual-qc-weights \
        --project "/content/drive/MyDrive/Visual QC Copilot"

Uploads results/exported_models/*.onnx and results/calibration_*.json, flat, with the same names.
"""
import argparse
from pathlib import Path

from huggingface_hub import HfApi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="e.g. arnesh/visual-qc-weights")
    parser.add_argument("--project", default="/content/drive/MyDrive/Visual QC Copilot")
    parser.add_argument("--only", nargs="*", help="tags to upload, e.g. patchcore_bottle padim_pcb1")
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    results = Path(args.project) / "results"
    files = sorted((results / "exported_models").glob("*.onnx")) + sorted(results.glob("calibration_*.json"))
    if args.only:
        files = [f for f in files if any(tag in f.name for tag in args.only)]
    if not files:
        raise SystemExit(f"Nothing to upload under {results}")

    api = HfApi()
    api.create_repo(args.repo, repo_type="model", private=args.private, exist_ok=True)
    for f in files:
        print(f"uploading {f.name} ({f.stat().st_size / 1e6:.1f} MB)")
        api.upload_file(path_or_fileobj=str(f), path_in_repo=f.name, repo_id=args.repo)
    print("done:", f"https://huggingface.co/{args.repo}")


if __name__ == "__main__":
    main()
