"""Parity check: does the served detector make the same decisions as your Colab notebook?

Point it at a folder with good/ and bad/ (or defective/) subfolders, e.g. the same 8 + 8 images
your notebook's ONNX check used, then compare the printed rows and the "Wrong decisions" line.

    python scripts/check_parity.py --product pcb --images path/to/check_images
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # run from anywhere: find qc_copilot/

from qc_copilot import imaging  # noqa: E402
from qc_copilot.detector import get_detector  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=["bottle", "pcb"], required=True)
    parser.add_argument("--images", required=True)
    args = parser.parse_args()

    det = get_detector(args.product)
    print(f"detector={det.backend} threshold={det.threshold:.4f}")
    if det.backend == "demo":
        raise SystemExit("Demo detector active: the ONNX model was not found. Check MODELS_DIR / HF_MODEL_REPO.")

    wrong = total = 0
    for sub in ("good", "bad", "defective"):
        folder = Path(args.images) / sub
        for path in sorted(p for p in folder.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}):
            d = det.predict(imaging.load_image(path.read_bytes()))
            truth_bad = sub != "good"
            ok = d.is_defective == truth_bad
            wrong += not ok
            total += 1
            print((sub, path.name, round(d.score, 3), "ALERT" if d.is_defective else "ok", "correct" if ok else "WRONG"))
    print(f"Wrong decisions: {wrong} of {total}")


if __name__ == "__main__":
    main()
