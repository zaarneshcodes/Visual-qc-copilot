# Setup guide: from zip to live demo

A step-by-step beginner version, including a no-install GitHub Codespaces route, is the Claude Doc
"Visual QC Copilot – Beginner Setup Guide". This file is the short reference.

Work through the phases in order. Each step says **where** you do it:

- 💻 **Terminal** — type the command and press Enter
- 📝 **Editor** — an action in VS Code
- 🌐 **Browser** — a website (GitHub, Hugging Face, Colab, Anthropic Console)

Where Windows and Mac/Linux differ, both are shown. Do not move on until the ✅ checkpoint passes.

| Phase | Result | Time |
|-------|--------|------|
| 0 | Accounts and tools ready | 20 min |
| 1 | App running locally in demo mode | 20 min |
| 2 | Code on GitHub with green CI | 15 min |
| 3 | Tracking set up (issues, milestones, board) | 15 min |
| 4 | Your Colab models served by the app, files on the HF Hub | 30 min |
| 5 | App live on Hugging Face Spaces, auto-deploying from GitHub | 30 min |

---

## Phase 0 — Accounts and tools

1. 🌐 Create accounts (free): GitHub (github.com), Hugging Face (huggingface.co), Anthropic Console (console.anthropic.com).
2. 🌐 In the Anthropic Console create an API key. Copy it somewhere private. It starts with `sk-ant-`.
3. Install tools:
   - **Python 3.11** — Windows: python.org installer, tick *Add python.exe to PATH*. Mac: `brew install python@3.11`. Ubuntu: `sudo apt install python3.11 python3.11-venv`.
   - **Git** — Windows: git-scm.com (keep defaults; it includes Git Credential Manager). Mac: `xcode-select --install`.
   - **VS Code** — code.visualstudio.com, plus the *Python* extension.
4. 💻 Tell git who you are (once per machine):
   ```bash
   git config --global user.name "Arnesh Nayak"
   git config --global user.email "the-email-on-your-github-account"
   git config --global init.defaultBranch main
   ```

✅ **Checkpoint 0**
```bash
python --version     # Mac/Linux may need: python3 --version   → 3.11.x
git --version
```

---

## Phase 1 — Run it locally

1. Unzip `visual-qc-copilot.zip` to a path **without spaces**:
   - Windows: `C:\dev\visual-qc-copilot`
   - Mac/Linux: `~/dev/visual-qc-copilot`
2. 📝 VS Code → *File → Open Folder* → choose that folder. Open a terminal inside VS Code with *Terminal → New Terminal*. Every command below runs from this folder.
3. 💻 Create and activate a virtual environment:

   | Windows (PowerShell) | Mac/Linux |
   |---|---|
   | `python -m venv .venv` | `python3 -m venv .venv` |
   | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |

   Your prompt now starts with `(.venv)`. If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.
4. 💻 Install the core dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```
5. 💻 Create your secrets file:

   | Windows | Mac/Linux |
   |---|---|
   | `copy .env.example .env` | `cp .env.example .env` |

6. 📝 Open `.env` and set:
   ```
   GEMINI_API_KEY=...your free key from aistudio.google.com...
   RAG_BACKEND=keyword
   ```
   (`keyword` for now because the semantic search stack is installed in Phase 4.)
7. 💻 Run the tests:
   ```bash
   ruff check .
   pytest -q
   ```

✅ **Checkpoint 1a** — `ruff` prints `All checks passed!` and pytest ends with `15 passed`.

8. 💻 **Terminal 1** (API):
   ```bash
   uvicorn qc_copilot.api:app --reload --port 8000
   ```
9. 💻 **Terminal 2** — click the **+** in the VS Code terminal panel, activate the venv again (step 3, second row), then:
   ```bash
   streamlit run dashboard/streamlit_app.py
   ```

✅ **Checkpoint 1b**
- 🌐 http://localhost:8000/health shows `"status": "ok"`, detectors `"demo (no patchcore_bottle.onnx)"`, and your Claude model under `llm`.
- 🌐 http://localhost:8501 opens the dashboard. Upload any bottle image from MVTec AD (`bottle/test/broken_large/000.png`) and click **Run inspection**. You get a heatmap and a verdict. If the score is above 0.5 you also get a Claude description.

Stop both servers with `Ctrl+C` when done.

---

## Phase 2 — Put it on GitHub

1. 🌐 GitHub → **+** (top right) → **New repository**.
   - Name: `visual-qc-copilot`
   - Public
   - **Do not** tick README, .gitignore or license (the project already has them).
   - Click **Create repository**.
2. 💻 In the project folder:
   ```bash
   git init
   git add .
   git status
   ```
   ✅ Look at the list. `.env`, `.venv/` and any `*.pt` file must **not** appear. If `.env` appears, stop and check `.gitignore` is in the folder.
3. 💻 First commit and push (replace `zaarneshcodes`):
   ```bash
   git commit -m "chore: initial project scaffold"
   git remote add origin https://github.com/zaarneshcodes/visual-qc-copilot.git
   git push -u origin main
   ```
   A browser window asks you to sign in to GitHub the first time (Windows: Git Credential Manager; Mac: use a Personal Access Token as the password if asked — GitHub → Settings → Developer settings → Personal access tokens → *Fine-grained*, repo access to this repository, *Contents: Read and write*, *Workflows: Read and write*).
4. 📝 In `README.md`, replace `zaarneshcodes` and `Zaarneshcodes`. Then 💻:
   ```bash
   git add README.md
   git commit -m "docs: set repository links"
   git push
   ```

✅ **Checkpoint 2** — 🌐 the repository page shows your files, and the **Actions** tab shows a green ✓ for the *CI* workflow. (*Deploy to Hugging Face Space* is skipped until Phase 5 — that is expected.)

---

## Phase 3 — Track the work

This is how you "keep track": GitHub Issues hold the tasks, Milestones group them, a Project board shows status, and `docs/PROGRESS.md` + `CHANGELOG.md` are the written record in the repo.

1. 🌐 Repo → **Issues → Milestones → New milestone**. Create the five milestones listed in `docs/PROGRESS.md` (M1 … M5).
2. 🌐 **Issues → New issue → Task**. Create one issue per unchecked item in `docs/PROGRESS.md` and set its milestone.
3. 🌐 Your profile → **Projects → New project → Board**. Name it *Visual QC Copilot*. Columns: *Todo, In progress, Done*. Add the issues.
4. Branch workflow for every task from now on — 💻:
   ```bash
   git checkout main
   git pull
   git checkout -b feat/short-task-name      # e.g. feat/pcb-training
   # ...make changes...
   git add .
   git commit -m "feat: what you did"       # prefixes: feat, fix, docs, chore, test, refactor
   git push -u origin feat/short-task-name
   ```
   🌐 GitHub shows **Compare & pull request**. Write `Closes #<issue number>` in the description, wait for CI to pass, then **Merge**. The issue closes and moves to *Done* by itself.
5. 📝 After each merge, tick the item in `docs/PROGRESS.md` and add a line under *Unreleased* in `CHANGELOG.md`. Record any design choice in `docs/DECISIONS.md` with a one-line reason.
6. At the end of each milestone 💻 tag a release:
   ```bash
   git tag -a v0.2.0 -m "M2: PatchCore weights integrated"
   git push --tags
   ```
   🌐 **Releases → Draft a new release** → choose the tag → paste the CHANGELOG section.

✅ **Checkpoint 3** — the board shows your issues, and one small change (for example ticking an item in `PROGRESS.md`) has gone through branch → PR → merge with green CI.

---

## Phase 4 — Serve your Colab models

Your notebooks already trained, calibrated and exported the models to `Drive/Visual QC Copilot/results/`.
The app reads the same file names: `{model}_{category}.onnx` and `calibration_{model}_{category}.json`
(for example `patchcore_bottle.onnx`). The `.onnx` files are large (PaDiM pcb1 is 177 MB), so they live in a
Hugging Face **model** repository, not in git.

1. 🌐 Hugging Face → avatar → **Settings → Access Tokens → Create new token** → type **Write** → name `visual-qc`. Copy it.
2. 🌐 Open `03_PCB_Benchmark.ipynb` in Colab (any runtime, GPU not needed), run the Drive-mount cell, then add and run the upload cell from `notebooks/README.md` (section *Publishing models for the app*).
3. 📝 Copy `results_log.csv`, all `calibration_*.json` and `runs/*.json` from Drive into the repo's `results/` folder (replace the two calibration files already there), and commit them on a branch.

✅ **Checkpoint 4a** — 🌐 `https://huggingface.co/Zaarneshcodes/visual-qc-weights` lists `patchcore_bottle.onnx`, `patchcore_pcb1.onnx`, `padim_bottle.onnx`, `padim_pcb1.onnx` and the four calibration files.

4. 💻 With the venv active, install semantic SOP search:
   ```bash
   pip install -r requirements-rag.txt
   ```
5. 📝 In `.env` set `HF_MODEL_REPO=Zaarneshcodes/visual-qc-weights` and `RAG_BACKEND=chroma`.
6. 💻 Restart terminal 1 (`uvicorn ...`). The first bottle and PCB inspections download their models (a minute each).
7. 💻 **Parity check (tracker 2.1 gate).** Copy the same 8 good + 8 defective pcb1 images your notebook's ONNX check used into `data/check/good/` and `data/check/bad/`. Then:
   ```bash
   python scripts/check_parity.py --product pcb --images data/check
   ```
   (For the PaDiM model add `MODEL_PCB=padim` to `.env` first, restart, and run again.)

✅ **Checkpoint 4b**
- http://localhost:8000/health shows `"pcb": "onnx:patchcore_pcb1"` after one PCB inspection, and `"rag_backend": "chroma"`.
- The parity check prints the same scores (to about 0.01) and the same `Wrong decisions: N of 16` as the notebook. If every score is off, set `ONNX_INPUT_NORM=imagenet` in `.env`, restart and rerun; keep whichever setting matches the notebook.
- Mark tracker 2.1 done.

---

## Phase 5 — Go live on Hugging Face Spaces

The Space runs the `Dockerfile`: FastAPI inside, Streamlit on port 7860 in front. GitHub Actions pushes every merge to `main` into the Space, so the live app always matches `main`.

1. 🌐 Hugging Face → **New → Space**.
   - Name: `visual-qc-copilot`
   - SDK: **Docker** → template **Blank**
   - Hardware: **CPU basic (free)**
   - Public → **Create Space**
2. 🌐 In the Space: **Settings → Variables and secrets**:
   - **New secret** `GEMINI_API_KEY` = your free Gemini key (or `ANTHROPIC_API_KEY` if you use Claude)
   - **New variable** `HF_MODEL_REPO` = `Zaarneshcodes/visual-qc-weights`
   - **New variable** `RAG_BACKEND` = `chroma`
   - **New variable** `MODEL_PCB` = `patchcore` (or `padim` for a much faster but less accurate PCB demo)
3. 🌐 GitHub repo → **Settings → Secrets and variables → Actions**:
   - *Secrets* tab → **New repository secret** `HF_TOKEN` = the Write token from Phase 4
   - *Variables* tab → **New repository variable** `HF_SPACE` = `Zaarneshcodes/visual-qc-copilot`
4. 🌐 GitHub → **Actions → Deploy to Hugging Face Space → Run workflow** (or just merge any PR into `main`).
5. 🌐 Back in the Space, the status goes *Building* (about 5 min) → *Running*. Click **Logs** to watch.

✅ **Checkpoint 5** — the Space URL shows the dashboard, the sidebar says *Detector: onnx:patchcore_bottle* after your first inspection, and a defective bottle image returns a FAIL or REVIEW verdict with SOP citations. Put this URL on your CV, LinkedIn and the top of the README.

Free Spaces sleep after about 48 hours without visitors and wake on the next visit (first load is slow). That is normal.

---

## Daily loop

```bash
git checkout main && git pull
git checkout -b feat/next-thing
# code → test locally (two terminals) → ruff check . && pytest -q
git add . && git commit -m "feat: ..." && git push -u origin feat/next-thing
# open PR → CI green → merge → Space redeploys automatically
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `python` not found (Windows) | PATH not set | Reinstall Python with *Add to PATH*, or use `py -3.11` instead of `python` |
| `Activate.ps1 cannot be loaded` | PowerShell policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Dashboard says *API not reachable* | Terminal 1 not running, or wrong `API_URL` | Start uvicorn; keep `API_URL=http://localhost:8000` in `.env` |
| `llm: offline` in /health | Key missing or `.env` not in project root | Check `.env` sits next to `README.md`, restart uvicorn |
| Claude errors in uvicorn log (401 / 404 model) | Bad key, or model name not available to your key | Regenerate key; set `CLAUDE_MODEL` to a model listed in your Console |
| `git push` rejected: *updates were rejected* | Repo created with a README | `git pull origin main --allow-unrelated-histories`, then push |
| Push asks for password and fails | GitHub no longer accepts passwords | Use a Personal Access Token as the password (Phase 2, step 3) |
| Deploy Action fails with 401/403 | `HF_TOKEN` is read-only or misspelled | Create a **Write** token and update the GitHub secret |
| Space push rejected: *binary files* | An image or `.pt` file was committed | `git rm --cached path/to/file`, add it to `.gitignore`, commit, push |
| Detector stays `demo (no ….onnx)` | File name or repo id mismatch | Names must be exactly `{model}_{category}.onnx`, e.g. `patchcore_pcb1.onnx`; check `HF_MODEL_REPO` |
| Parity check scores all differ from the notebook | Input preprocessing differs | Toggle `ONNX_INPUT_NORM` between `none` and `imagenet` |
| `INVALID_ARGUMENT ... batch` from onnxruntime | Unexpected fixed batch size | Paste the error in chat with the run JSON's `onnx_signature` |
| Upload fails with 403 on the Space | Streamlit XSRF behind proxy | Already disabled in `start.sh`; check you did not edit those flags |
| PCB inspection takes ~4 s on the Space | PatchCore pcb1 is ~3.9 s per image on CPU | Expected; set `MODEL_PCB=padim` (~0.12 s) for a snappier demo |
| `pytest` fails only on your machine | `.env` overrides test settings | Tests force demo/keyword mode; run `pytest -q` from the project root |
