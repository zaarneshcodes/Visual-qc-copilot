# Advanced computer vision: what matters in industry, and how to practise it

Notes written as a research supervisor would brief an M.Tech student who already trains YOLO and wants
industry-grade depth. Model names move fast; check the latest release of each before you build on it.

## 1. The mental model industry uses

A deployed vision system is a pipeline, and the model is usually the smallest part of it:

```
capture → data curation & labelling → training → evaluation → optimisation → serving → monitoring → retraining
```

Hiring managers look for evidence that you have touched the stages around the model: how you chose a
threshold, what latency you measured, what happens when the lighting changes. That is the gap most student
portfolios leave open.

## 2. Techniques worth knowing deeply

| Area | What to learn | Why industry cares | Tools |
|------|---------------|--------------------|-------|
| Foundation backbones | ViT, DINOv2/DINOv3 features, CLIP/SigLIP embeddings | Strong features with little labelled data; linear probes and k-NN often beat training from scratch | `timm`, Hugging Face `transformers` |
| Detection | Real-time detectors (YOLO11-class, RT-DETR, RF-DETR); open-vocabulary detection (Grounding DINO, OWLv2, YOLO-World) | Open-vocabulary models bootstrap labels for new classes in hours instead of weeks | Ultralytics, `supervision`, HF |
| Segmentation | Mask2Former; promptable segmentation (SAM 2 for video, SAM 3 for concept prompts) | Auto-labelling masks, measuring defect area, video object tracking | `segment-anything`, CVAT + SAM |
| Anomaly detection | PatchCore, PaDiM, EfficientAD; zero/few-shot (WinCLIP, AnomalyCLIP); metrics AUROC, PRO, F1 at fixed false-alarm rate | Factories have thousands of good parts and a handful of defects; one-class methods fit that reality | Anomalib; datasets MVTec AD, MVTec AD 2, VisA, Real-IAD |
| Vision-language models | Prompting with visual grounding, structured JSON output, LoRA fine-tuning of open VLMs (Qwen-VL family, PaliGemma, Florence-2) | Turning pixels into reports, queries and decisions operators can act on | Claude/GPT APIs, HF `peft`, `trl` |
| Video | Multi-object tracking (ByteTrack, BoT-SORT), re-identification, temporal action detection | Safety compliance, counting, process monitoring — and close to your annotation background | `supervision`, DeepStream |
| 3D and depth | Monocular depth (Depth Anything), stereo, point clouds, 3D Gaussian Splatting | Bin picking, volume estimation, digital twins | Open3D, `nerfstudio` |
| Data-centric methods | Active learning, label-error detection, synthetic data and domain randomisation, diffusion augmentation | Data quality moves accuracy more than architecture changes do | FiftyOne, cleanlab, Isaac Sim Replicator |
| Model optimisation | ONNX export, INT8 post-training quantisation vs QAT, pruning, distillation | Edge boxes and CPUs are where factory models run | ONNX Runtime, OpenVINO, TensorRT |
| Serving and MLOps | Batching, model registries, experiment tracking, data versioning, drift monitoring | Separates a demo from a system someone can maintain | Triton, FastAPI, MLflow or W&B, DVC |

## 3. How to turn this into industrial experience

**Make Visual QC Copilot evaluation-grade (M4 in PROGRESS.md).** Report PRO and pixel AUROC as well as image
AUROC. Pick thresholds at a stated false-alarm budget (for example 1% of good units flagged). Measure CPU
latency before and after OpenVINO export. Write a short failure analysis with heatmaps. This turns a demo into
an engineering study.

**Build a second, contrasting project in video.** Your annotation internship is an asset here. A good choice:
PPE or zone-compliance monitoring on CCTV-style footage — detector + tracker + rules, exported to ONNX/TensorRT,
with a measured FPS on a modest GPU or Jetson. Include the labelling workflow (CVAT, SAM-assisted masks,
label QA in FiftyOne), because that is real industrial work most candidates skip.

**Do one edge-deployment benchmark.** Same model in FP32, FP16 and INT8 across PyTorch, ONNX Runtime and
OpenVINO/TensorRT; a table of accuracy vs latency vs memory. Small project, very high signal.

**Connect it to your thesis.** The M4 evaluation (detector + VLM + RAG on MVTec AD 2 or VisA, with the VLM's
grounding measured) is a credible workshop-paper scope. The Visual Anomaly and Novelty Detection (VAND)
workshop at CVPR is the natural venue; discuss it with your supervisor early.

**Contribute upstream.** A documented bug fix or example notebook in Anomalib, Ultralytics, `supervision` or
FiftyOne is public proof that you can work in a production codebase with reviews and CI.

**Get near real data.** Manufacturing clusters around Delhi NCR (auto components, electronics, packaging) have
inspection problems and little ML staff. A short, scoped pilot with a plant — even 200 images under an NDA —
beats any public dataset on a CV. Offer a defined deliverable: a baseline model, a threshold study, and a
report.

## 4. A 12-week plan

| Weeks | Focus | Output |
|-------|-------|--------|
| 1–3 | Visual QC Copilot M1–M3 | Live demo, real weights, README with results |
| 4–5 | Evaluation study (M4) | Metrics tables, failure analysis, blog post |
| 6–8 | Video compliance project | Repo + demo video + FPS table |
| 9–10 | Edge benchmark | Quantisation comparison write-up |
| 11–12 | Upstream PR + workshop draft | Merged PR link; paper draft for supervisor review |

## 5. Reading list, in order

1. Roth et al., *Towards Total Recall in Industrial Anomaly Detection* (PatchCore), CVPR 2022
2. Defard et al., *PaDiM*, ICPR workshops 2021
3. Batzner et al., *EfficientAD*, WACV 2024
4. Bergmann et al., MVTec AD papers (IJCV 2021) and the MVTec AD 2 release
5. Jeong et al., *WinCLIP*, CVPR 2023
6. Oquab et al., *DINOv2*, 2023
7. Kirillov et al., *Segment Anything*, ICCV 2023, then the SAM 2 paper
8. Lewis et al., *Retrieval-Augmented Generation*, NeurIPS 2020
9. Sculley et al., *Hidden Technical Debt in Machine Learning Systems*, NeurIPS 2015
