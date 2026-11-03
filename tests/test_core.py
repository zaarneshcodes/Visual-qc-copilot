import numpy as np

from qc_copilot import imaging, pipeline, rag
from qc_copilot.detector import DemoDetector, get_detector


def test_demo_detector_scores_defect_higher(good_png, defect_png):
    det = DemoDetector(threshold=0.5)
    good = det.predict(imaging.load_image(good_png))
    bad = det.predict(imaging.load_image(defect_png))
    assert 0.0 <= good.score <= 1.0 and 0.0 <= bad.score <= 1.0
    assert bad.score > good.score


def test_region_stats_finds_hotspot():
    amap = np.zeros((100, 100))
    amap[5:20, 80:95] = 1.0
    stats = imaging.defect_region_stats(amap)
    assert stats["location"] == "top-right"
    assert 0 < stats["area_fraction"] < 0.1


def test_sops_are_chunked_and_searchable():
    chunks = rag.load_chunks()
    assert any(c.source == "SOP-BTL-001.md" for c in chunks)
    hits = rag.KeywordRetriever(chunks).search("solder bridge disposition", k=3, product="pcb")
    assert hits and hits[0].source == "SOP-PCB-001.md"


def test_pipeline_runs_offline(defect_png):
    get_detector("bottle")
    result = pipeline.inspect(defect_png, "bottle")
    assert result["detection"]["backend"] == "demo"
    assert result["report"]["verdict"] in {"PASS", "FAIL", "REVIEW"}
    assert result["images"]["overlay_png_b64"]
    assert "QC inspection report" in pipeline.report_markdown(result)
