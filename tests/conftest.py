"""Force offline, dependency-light settings BEFORE the app modules are imported."""
import io
import os

os.environ["DETECTOR_MODE"] = "demo"
os.environ["RAG_BACKEND"] = "keyword"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_PROVIDER"] = "none"

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def _png(defect: bool) -> bytes:
    rng = np.random.default_rng(0)
    base = (120 + rng.normal(0, 4, (256, 256, 3))).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(base)
    if defect:
        ImageDraw.Draw(img).line([(60, 60), (110, 140)], fill=(10, 10, 10), width=4)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def good_png() -> bytes:
    return _png(defect=False)


@pytest.fixture
def defect_png() -> bytes:
    return _png(defect=True)
