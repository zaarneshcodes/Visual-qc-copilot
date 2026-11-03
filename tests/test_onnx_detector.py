"""OnnxDetector logic tested with a fake onnxruntime session (no model file or onnxruntime needed)."""
import json
from types import SimpleNamespace

import numpy as np
from PIL import Image

from qc_copilot.detector import OnnxDetector, load_threshold


class FakeSession:
    def __init__(self, batch, score_shape):
        self.batch, self.score_shape, self.last_input = batch, score_shape, None

    def get_inputs(self):
        return [SimpleNamespace(name="input", shape=[self.batch, 3, "height", "width"])]

    def get_outputs(self):
        return [SimpleNamespace(name=n) for n in ("pred_score", "pred_label", "anomaly_map", "pred_mask")]

    def run(self, _, feed):
        x = feed["input"]
        self.last_input = x
        n = x.shape[0]
        return [np.full(self.score_shape(n), 0.7, np.float32), np.ones(n, bool),
                np.random.rand(n, 1, 256, 256).astype(np.float32), np.zeros((n, 1, 256, 256), bool)]


def _img():
    return Image.fromarray(np.full((300, 400, 3), 128, np.uint8))


def test_fixed_batch_of_two_like_bottle_export(tmp_path):
    sess = FakeSession(2, lambda n: (n,))
    det = OnnxDetector(tmp_path / "patchcore_bottle.onnx", threshold=0.4013, session=sess)
    d = det.predict(_img())
    assert sess.last_input.shape == (2, 3, 300, 400)  # full size, duplicated to fill the batch
    assert 0.49 < sess.last_input.max() < 0.51  # raw 0..1 pixels, no ImageNet normalisation
    assert d.is_defective and d.anomaly_map.shape == (256, 256)
    assert d.backend == "onnx:patchcore_bottle"


def test_dynamic_batch_like_pcb_export(tmp_path):
    sess = FakeSession("batch_size", lambda n: (n, 1))
    d = OnnxDetector(tmp_path / "padim_pcb1.onnx", threshold=0.8, session=sess).predict(_img())
    assert sess.last_input.shape[0] == 1
    assert abs(d.score - 0.7) < 1e-6 and not d.is_defective


def test_threshold_policies(tmp_path):
    f = tmp_path / "calibration_patchcore_pcb1.json"
    f.write_text(json.dumps({"threshold_balanced": 0.5, "threshold_zero_false_alarm_cal": 0.75}))
    assert load_threshold(f, "balanced", 0.1) == 0.5
    assert load_threshold(f, "zero_false_alarm", 0.1) == 0.75
    assert load_threshold(tmp_path / "missing.json", "balanced", 0.1) == 0.1
