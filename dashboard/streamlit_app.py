"""Streamlit dashboard. Run locally (terminal 2):  streamlit run dashboard/streamlit_app.py

Talks to the FastAPI service at API_URL (default http://localhost:8000), so the API must be running.
"""
from __future__ import annotations

import base64
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
VERDICT_STYLE = {
    "PASS": ("#2E7D4F", "Unit meets the SOP criteria"),
    "FAIL": ("#B3261E", "Follow the disposition below"),
    "REVIEW": ("#9A6A14", "Route to a human inspector"),
}

st.set_page_config(page_title="Visual QC Copilot", page_icon="🔍", layout="wide")
st.markdown(
    """
    <style>
      .verdict {border-left: 8px solid var(--c); padding: 0.7rem 1rem; margin-bottom: 0.8rem;
                background: rgba(28,37,43,0.04);}
      .verdict b {font-size: 1.7rem; color: var(--c);}
      .verdict span {display: block; opacity: 0.85;}
      .demo-note {font-size: 0.85rem; padding: 0.4rem 0.6rem; border: 1px dashed #9A6A14;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30, show_spinner=False)
def get_health() -> dict | None:
    try:
        return requests.get(f"{API_URL}/health", timeout=90).json()
    except requests.RequestException:
        return None


def show_b64(b64: str, caption: str) -> None:
    st.image(base64.b64decode(b64), caption=caption, use_container_width=True)


# ---------- Sidebar: station setup and system status ----------
with st.sidebar:
    st.header("Inspection station")
    product = st.selectbox("Product line", ["bottle", "pcb"], format_func=lambda p: "PCB" if p == "pcb" else "Bottle")
    health = get_health()
    st.subheader("System status")
    if health is None:
        st.error(f"API not reachable at {API_URL}. Start it with `uvicorn qc_copilot.api:app --port 8000`.")
    else:
        backend = health["detectors"].get(product, "?")
        st.write(f"Detector: **{backend}**")
        st.write(f"Language model: **{health['llm']}**")
        st.write(f"SOP search: **{health['rag_backend']}** ({health.get('sop_chunks')} sections)")
        if "demo" in backend:
            st.markdown(
                '<div class="demo-note">Demo detector active: scores come from a simple texture heuristic, '
                "not a trained model. Set HF_MODEL_REPO or put the .onnx files in models/ for real results.</div>",
                unsafe_allow_html=True,
            )

st.title("Visual QC Copilot")
st.caption("Upload a photo of one unit. The copilot scores it for anomalies, describes any defect and applies your SOPs.")

tab_inspect, tab_history = st.tabs(["Inspect a unit", "Recent inspections"])

with tab_inspect:
    upload = st.file_uploader("Unit photo (PNG or JPEG)", type=["png", "jpg", "jpeg"])
    if upload is None:
        st.info("Start with an image from the MVTec AD bottle or VisA pcb1 test set.")
    elif st.button("Run inspection", type="primary", disabled=health is None):
        with st.spinner("Scoring, describing and checking SOPs…"):
            resp = None
            try:
                resp = requests.post(
                    f"{API_URL}/inspect",
                    files={"file": (upload.name, upload.getvalue(), upload.type)},
                    data={"product": product},
                    timeout=180,
                )
                resp.raise_for_status()
                st.session_state["result"] = resp.json()
            except requests.HTTPError:
                st.error(f"Inspection failed: {resp.json().get('detail', resp.text)}")
            except requests.RequestException as exc:
                st.error(f"Could not reach the API: {exc}")

    result = st.session_state.get("result")
    if result:
        det, desc, rep = result["detection"], result["description"], result["report"]
        left, right = st.columns(2)
        with left:
            view = st.radio("View", ["Heatmap overlay", "Heatmap only"], horizontal=True, label_visibility="collapsed")
            key = "overlay_png_b64" if view == "Heatmap overlay" else "heatmap_png_b64"
            show_b64(result["images"][key], f"Red marks the most anomalous region (score {det['score']:.3f})")
        with right:
            color, line = VERDICT_STYLE.get(rep.get("verdict"), VERDICT_STYLE["REVIEW"])
            st.markdown(
                f'<div class="verdict" style="--c:{color}"><b>{rep.get("verdict", "REVIEW")}</b><span>{line}</span></div>',
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("Anomaly score", f"{det['score']:.3f}", help=f"Flagged at {det['threshold']} or above")
            c2.metric("Severity", str(rep.get("severity", "–")).title())
            c3.metric("Disposition", str(rep.get("disposition", "–")).title())
            st.subheader("What the inspector sees")
            st.write(desc.get("visual_description", ""))
            st.subheader("Summary")
            st.write(rep.get("summary", ""))
            if rep.get("actions"):
                st.subheader("Next actions")
                for i, action in enumerate(rep["actions"], 1):
                    st.write(f"{i}. {action}")
        with st.expander("SOP rules applied"):
            for c in rep.get("sop_citations", []):
                st.write(f"**{c.get('sop')}**, {c.get('section')}: {c.get('rule')}")
        with st.expander("Raw result (JSON)"):
            st.json({k: v for k, v in result.items() if k != "images"})
        try:
            md = requests.get(f"{API_URL}/history/{result['id']}/report.md", timeout=30)
            if md.ok:
                st.download_button("Download report", md.text, file_name=f"qc-report-{result['id']}.md")
        except requests.RequestException:
            pass

with tab_history:
    if health is None:
        st.write("Connect the API to see recent inspections.")
    else:
        rows = requests.get(f"{API_URL}/history", timeout=30).json()
        if not rows:
            st.write("No inspections yet. Results appear here after your first run and reset when the API restarts.")
        else:
            st.dataframe(
                [
                    {
                        "time (UTC)": r["timestamp"],
                        "product": r["product"],
                        "verdict": r["report"].get("verdict"),
                        "score": r["detection"]["score"],
                        "detector": r["detection"]["backend"],
                        "id": r["id"],
                    }
                    for r in rows
                ],
                use_container_width=True,
            )
