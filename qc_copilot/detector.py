"""Layer 1 — anomaly detection from the ONNX models exported by the Colab notebooks.

Expected files in MODELS_DIR (same names the notebooks write to Drive):
    {model}_{category}.onnx                 e.g. patchcore_bottle.onnx, padim_pcb1.onnx
    calibration_{model}_{category}.json     threshold_balanced / threshold_zero_false_alarm_cal

The Anomalib 2.x export contains its own resize + normalisation, so the input is the
full-size RGB image as float32 in 0..1, NCHW. Batch may be dynamic or fixed (e.g. 2);
both are handled. DemoDetector keeps the app and CI running when no model is present.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image, ImageFilter

from .config import PRODUCT_CATEGORY, ROOT_DIR, SUPPORTED_PRODUCTS, settings

log = logging.getLogger(__name__)

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], np.float32)


@dataclass
class Detection:
    score: float  # Anomalib pred_score scale (same scale the calibration was done on)
    is_defective: bool
    anomaly_map: np.ndarray  # 2-D float array
    backend: str  # e.g. "onnx:patchcore_bottle" or "demo"
    threshold: float


class Detector(Protocol):
    backend: str
    threshold: float

    def predict(self, image: Image.Image) -> Detection: ...


def load_threshold(calibration: Path, policy: str, default: float) -> float:
    if not calibration.exists():
        log.warning("No calibration file %s; using ANOMALY_THRESHOLD=%s", calibration.name, default)
        return default
    data = json.loads(calibration.read_text())
    key = "threshold_zero_false_alarm_cal" if policy == "zero_false_alarm" else "threshold_balanced"
    return float(data.get(key, default))


class OnnxDetector:
    def __init__(self, model_path: Path, threshold: float, input_norm: str = "none", session=None):
        if session is None:
            import onnxruntime as ort

            session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        self.session = session
        self.threshold = threshold
        self.input_norm = input_norm
        self.backend = f"onnx:{model_path.stem}"
        inp = session.get_inputs()[0]
        self.input_name = inp.name
        shape = list(inp.shape)
        self.fixed_batch = shape[0] if isinstance(shape[0], int) else 1
        self.fixed_hw = (shape[2], shape[3]) if all(isinstance(s, int) for s in shape[2:4]) else None
        self.output_names = [o.name for o in session.get_outputs()]
        log.info("Loaded %s (batch=%s, hw=%s, threshold=%.4f)", model_path.name, self.fixed_batch, self.fixed_hw, threshold)

    def prepare(self, image: Image.Image) -> np.ndarray:
        img = image.convert("RGB")
        if self.fixed_hw:
            img = img.resize((self.fixed_hw[1], self.fixed_hw[0]), Image.BILINEAR)
        arr = np.asarray(img, np.float32) / 255.0
        if self.input_norm == "imagenet":  # only if a parity check shows the graph lacks normalisation
            arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
        x = arr.transpose(2, 0, 1)[None]
        return np.repeat(x, self.fixed_batch, axis=0).astype(np.float32)

    def predict(self, image: Image.Image) -> Detection:
        outputs = dict(zip(self.output_names, self.session.run(None, {self.input_name: self.prepare(image)}), strict=False))
        score = float(np.ravel(outputs["pred_score"])[0])
        amap = np.asarray(outputs.get("anomaly_map", np.zeros((1, 1, 256, 256))), np.float32)[0].squeeze()
        return Detection(score, score >= self.threshold, amap, self.backend, self.threshold)


class DemoDetector:
    """NOT a trained model: flags local texture deviations. Exercises the pipeline only."""

    backend = "demo"

    def __init__(self, threshold: float):
        self.threshold = threshold

    def predict(self, image: Image.Image) -> Detection:
        gray = image.convert("L").resize((256, 256))
        smooth = gray.filter(ImageFilter.MedianFilter(size=9))
        diff = np.abs(np.asarray(gray, np.float32) - np.asarray(smooth, np.float32))
        diff = np.asarray(Image.fromarray(diff.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32)
        p99, median = np.percentile(diff, 99.5), np.median(diff) + 1e-6
        score = float(np.clip((p99 / median - 1.0) / 8.0, 0.0, 1.0))
        return Detection(score, score >= self.threshold, diff, self.backend, self.threshold)


def model_tag(product: str) -> str:
    return f"{settings.model_for(product)}_{PRODUCT_CATEGORY[product]}"


def _paths(product: str) -> tuple[Path, Path]:
    """Model from MODELS_DIR; calibration from MODELS_DIR, else the copy committed in results/."""
    tag = model_tag(product)
    calib = settings.models_dir / f"calibration_{tag}.json"
    if not calib.exists():
        calib = ROOT_DIR / "results" / calib.name
    return settings.models_dir / f"{tag}.onnx", calib


def _maybe_download(product: str) -> None:
    """Fetch the .onnx (and calibration, if no local copy) from a Hugging Face model repo."""
    if not settings.hf_model_repo:
        return
    from huggingface_hub import hf_hub_download

    model_path, calib_path = _paths(product)
    wanted = [model_path] + ([] if calib_path.exists() else [calib_path])
    for path in wanted:
        if path.exists():
            continue
        try:
            hf_hub_download(repo_id=settings.hf_model_repo, filename=path.name, local_dir=str(settings.models_dir))
            log.info("Downloaded %s from %s", path.name, settings.hf_model_repo)
        except Exception as exc:
            log.warning("Could not download %s: %s", path.name, exc)


_cache: dict[str, Detector] = {}


def get_detector(product: str) -> Detector:
    if product not in SUPPORTED_PRODUCTS:
        raise ValueError(f"Unknown product '{product}'. Use one of: {', '.join(SUPPORTED_PRODUCTS)}")
    if product in _cache:
        return _cache[product]

    detector: Detector | None = None
    if settings.detector_mode != "demo":
        _maybe_download(product)
        model_path, calib_path = _paths(product)  # re-resolve: a download may have added files
        if model_path.exists():
            threshold = load_threshold(calib_path, settings.threshold_policy, settings.anomaly_threshold)
            try:
                detector = OnnxDetector(model_path, threshold, settings.onnx_input_norm)
            except Exception as exc:
                log.error("ONNX model failed to load for %s (%s); using demo detector", product, exc)
    if detector is None:
        detector = DemoDetector(settings.anomaly_threshold)
    _cache[product] = detector
    return detector


def detector_status() -> dict[str, str]:
    out = {}
    for product in SUPPORTED_PRODUCTS:
        if product in _cache:
            out[product] = _cache[product].backend
        elif settings.detector_mode == "demo":
            out[product] = "demo"
        else:
            model_path, _ = _paths(product)
            out[product] = f"onnx:{model_path.stem}" if model_path.exists() else f"demo (no {model_path.name})"
    return out
