import os
import tempfile

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from pdf_engine import TEMPLATES, generate_pdf

from .auth import get_api_key_record
from .models import GenerateRequest

app = FastAPI(
    title="Styled PDF Generator API",
    description="Generate bordered, tab-labeled PDFs (notes, invoices, certificates, receipts, memos, worksheets) from JSON.",
    version="0.1.0",
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/v1/templates")
def list_templates():
    return {"templates": sorted(TEMPLATES.keys())}


@app.post("/v1/generate")
def generate(req: GenerateRequest, key_record: dict = Depends(get_api_key_record)):
    if req.template not in TEMPLATES:
        raise HTTPException(400, f"Unknown template {req.template!r}; choose one of {sorted(TEMPLATES)}")

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        generate_pdf(
            tmp_path,
            req.text_lines,
            template=req.template,
            tab_text=req.tab_text,
            tab_fill_color=req.tab_fill_color,
            tab_text_color=req.tab_text_color,
            tab_font=req.tab_font,
            body_font=req.body_font,
        )
    except Exception:
        os.remove(tmp_path)
        raise

    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename="generated.pdf",
        background=BackgroundTask(os.remove, tmp_path),
    )
