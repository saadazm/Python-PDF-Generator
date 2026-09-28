import csv
import io
import os
import tempfile
import zipfile

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from pdf_engine import TEMPLATES, generate_pdf

from .auth import charge_quota, get_api_key_record, require_api_key
from .models import GenerateRequest

MAX_BATCH_ROWS = 500

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


def _apply_brand(req: GenerateRequest, brand: dict) -> dict:
    """Merge a key's white-label brand profile under explicit request fields.

    Precedence: request field (if set) > key's brand profile > pdf_engine's
    template preset. This lets a B2B customer's PDFs come out on-brand by
    default while still letting a single call override anything.
    """
    fields = ("tab_text", "tab_fill_color", "tab_text_color", "tab_font", "body_font")
    merged = {}
    for field in fields:
        req_value = getattr(req, field)
        merged[field] = req_value if req_value is not None else brand.get(field)
    merged["logo_path"] = brand.get("logo_path")
    return merged


@app.post("/v1/generate")
def generate(req: GenerateRequest, key_record: dict = Depends(get_api_key_record)):
    if req.template not in TEMPLATES:
        raise HTTPException(400, f"Unknown template {req.template!r}; choose one of {sorted(TEMPLATES)}")

    brand = key_record.get("brand") or {}
    merged = _apply_brand(req, brand)

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        generate_pdf(
            tmp_path,
            req.text_lines,
            template=req.template,
            **merged,
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


@app.post("/v1/generate/batch")
async def generate_batch(
    file: UploadFile = File(..., description="CSV with 'filename' and 'text' columns (use \\n inside 'text' for multiple body lines)"),
    template: str = Form("note"),
    api_key: str = Depends(require_api_key),
):
    if template not in TEMPLATES:
        raise HTTPException(400, f"Unknown template {template!r}; choose one of {sorted(TEMPLATES)}")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "filename" not in reader.fieldnames or "text" not in reader.fieldnames:
        raise HTTPException(400, "CSV must have 'filename' and 'text' columns")
    rows = list(reader)
    if not rows:
        raise HTTPException(400, "CSV has no data rows")
    if len(rows) > MAX_BATCH_ROWS:
        raise HTTPException(400, f"Batch is limited to {MAX_BATCH_ROWS} rows; got {len(rows)}")

    # Charges (and quota-checks) the whole batch atomically before doing any
    # rendering work, so a request that can't be fully paid for fails fast.
    key_record = charge_quota(api_key, len(rows))
    brand = key_record.get("brand") or {}

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, row in enumerate(rows):
            raw_name = (row.get("filename") or f"document_{i + 1}").strip()
            safe_name = os.path.basename(raw_name) or f"document_{i + 1}"
            if not safe_name.lower().endswith(".pdf"):
                safe_name += ".pdf"
            body_lines = (row.get("text") or "").split("\n")

            fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            try:
                generate_pdf(
                    tmp_path,
                    body_lines,
                    template=template,
                    tab_fill_color=brand.get("tab_fill_color"),
                    tab_text_color=brand.get("tab_text_color"),
                    tab_font=brand.get("tab_font"),
                    body_font=brand.get("body_font"),
                    tab_text=brand.get("tab_text"),
                    logo_path=brand.get("logo_path"),
                )
                zf.write(tmp_path, arcname=safe_name)
            finally:
                os.remove(tmp_path)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=batch.zip"},
    )
