### **📄 Styled PDF Generator with Tab Label in Python**

This project generates PDFs with a **bordered content area** and a **custom tab-style label** embedded into the top border — via a standalone script, or as a hosted API with auth, quotas, white-label branding, and batch generation.

#### **Features**

* **Custom page border** with adjustable margins.
* **Tab-style header label** that visually “cuts” into the top border for a professional look.
* **Icon + text inside the tab** for branding or thematic emphasis.
* **Customizable colors, fonts, and sizes** for the tab and text.
* **Multi-line body text**, automatically word-wrapped and paginated across pages.
* **Six templates**: `note`, `invoice`, `certificate`, `receipt`, `memo`, `worksheet`.

#### **How It Works**

1. Sets up **A4 page layout** using ReportLab.
2. Draws a **main rectangular border** for the content area.
3. “Masks” part of the border to embed the tab.
4. Draws a **rounded rectangle tab** with a background fill color.
5. Places an **image icon** next to the tab label text.
6. Word-wraps and paginates body text lines inside the bordered area, adding new pages as needed.
7. Saves the output as a PDF.

#### **Requirements**

```bash
pip install -r requirements.txt
```

#### **Usage (CLI script)**

* Place your icon file (`lightbulb.gif` or any supported image format) in the same folder as the script.
* Run:

```bash
python generatepdf.py
```

* The generated PDF will be saved as `generated.pdf` in the same folder.

#### **Example Output**

* A clean **A4 PDF** with:

  * Light peach tab background (`#FFF0E9`)
  * Orange text color for the label (`#D38200`)
  * Black border around the content area
  * Example body text: `"Start....... "`

---

### **Project layout**

```
pdf_engine.py       Core rendering engine (templates, wrapping, pagination)
generatepdf.py       Thin CLI wrapper around pdf_engine, for local one-off use
api/                 FastAPI service exposing pdf_engine over HTTP
  main.py            Routes: /v1/generate, /v1/generate/batch, /v1/templates
  auth.py            X-API-Key validation + per-key monthly quota
  models.py          Request schema
  api_keys.json       Demo API keys (replace before deploying, see DEPLOY.md)
static/builder.html   No-code web UI for generating a PDF via the API
tests/                pytest suite for both the engine and the API
DEPLOY.md            Runbook for deploying the API to your own VPS
MARKETPLACE.md        Checklist for listing the API on RapidAPI
```

### **Running the API locally**

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Then open `http://127.0.0.1:8000/` for the no-code builder UI, or call it directly:

```bash
curl -X POST http://127.0.0.1:8000/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-free-key" \
  -d '{"text_lines": ["Hello from the API"], "template": "note"}' \
  -o generated.pdf
```

| Endpoint              | Method | Purpose                                                    |
|-----------------------|--------|-------------------------------------------------------------|
| `/v1/generate`        | POST   | JSON in, one PDF out.                                       |
| `/v1/generate/batch`  | POST   | CSV upload (`filename,text` columns) in, a zip of PDFs out. |
| `/v1/templates`       | GET    | List available templates.                                    |
| `/healthz`            | GET    | Liveness check.                                              |
| `/builder/builder.html` | GET  | No-code web UI (also served at `/`).                          |

Auth is a `X-API-Key` header checked against `api/api_keys.json`, which
also tracks each key's monthly quota (`demo-free-key`: 20/mo,
`demo-pro-key`: 2000/mo plus a sample white-label brand profile).
Exceeding quota returns `402`. **Replace the demo keys before deploying
anywhere real** — see `DEPLOY.md`.

### **Testing**

```bash
pip install -r requirements-dev.txt
pytest
```

### **Deploying and monetizing**

* `DEPLOY.md` — runbook for running this on your own VPS (systemd + nginx + HTTPS).
* `MARKETPLACE.md` — checklist for listing the API on RapidAPI, with a starting pricing table.
