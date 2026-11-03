"""Image utilities shared by the detector, VLM layer and API. Depends only on numpy + Pillow."""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

MAX_SIDE = 1024  # display / VLM copy only; the detector gets the full-size image


def load_image(data: bytes) -> Image.Image:
    """Decode uploaded bytes into a full-size RGB image (what the ONNX models were validated on)."""
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGB")


def display_copy(img: Image.Image) -> Image.Image:
    """Downscaled copy for overlays and VLM payloads."""
    out = img.copy()
    if max(out.size) > MAX_SIDE:
        out.thumbnail((MAX_SIDE, MAX_SIDE))
    return out


def normalise(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-8:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def jet_colormap(values: np.ndarray) -> np.ndarray:
    """Map a 0..1 array to RGB uint8 with a jet-style colormap (no matplotlib needed)."""
    v = np.clip(values, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4 * v - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * v - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * v - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def heatmap_image(anomaly_map: np.ndarray, size: tuple[int, int]) -> Image.Image:
    """Turn a 2-D anomaly map into a coloured heatmap resized to `size` (w, h)."""
    amap = normalise(np.squeeze(anomaly_map))
    heat = Image.fromarray(jet_colormap(amap))
    return heat.resize(size, Image.BILINEAR)


def overlay(image: Image.Image, anomaly_map: np.ndarray, alpha: float = 0.45) -> Image.Image:
    heat = heatmap_image(anomaly_map, image.size)
    return Image.blend(image.convert("RGB"), heat, alpha)


def to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def to_base64_png(image: Image.Image) -> str:
    return base64.b64encode(to_png_bytes(image)).decode("ascii")


def defect_region_stats(anomaly_map: np.ndarray, threshold: float = 0.6) -> dict:
    """Describe where the anomaly is: bounding box (fractions of width/height) and area share.

    Gives the VLM and the report a grounded, numeric location instead of a guess.
    """
    amap = normalise(np.squeeze(anomaly_map))
    mask = amap >= threshold
    if not mask.any():
        return {"area_fraction": 0.0, "bbox": None, "location": "none"}
    ys, xs = np.where(mask)
    h, w = amap.shape
    bbox = [round(xs.min() / w, 3), round(ys.min() / h, 3), round(xs.max() / w, 3), round(ys.max() / h, 3)]
    cx, cy = xs.mean() / w, ys.mean() / h
    vert = "top" if cy < 1 / 3 else "bottom" if cy > 2 / 3 else "middle"
    horiz = "left" if cx < 1 / 3 else "right" if cx > 2 / 3 else "centre"
    return {
        "area_fraction": round(float(mask.mean()), 4),
        "bbox": bbox,  # [x_min, y_min, x_max, y_max] as fractions of the image
        "location": f"{vert}-{horiz}",
    }
