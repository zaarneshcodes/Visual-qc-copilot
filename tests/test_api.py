from fastapi.testclient import TestClient

from qc_copilot.api import app

client = TestClient(app)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert set(body["detectors"]) == {"bottle", "pcb"}


def test_inspect_and_report(defect_png):
    resp = client.post("/inspect", files={"file": ("x.png", defect_png, "image/png")}, data={"product": "pcb"})
    assert resp.status_code == 200
    rid = resp.json()["id"]
    assert client.get("/history").json()[0]["id"] == rid
    assert client.get(f"/history/{rid}/report.md").status_code == 200


def test_rejects_unknown_product(good_png):
    resp = client.post("/inspect", files={"file": ("x.png", good_png, "image/png")}, data={"product": "car"})
    assert resp.status_code == 422


def test_rejects_non_image():
    resp = client.post("/inspect", files={"file": ("x.txt", b"hello", "text/plain")}, data={"product": "bottle"})
    assert resp.status_code == 400
