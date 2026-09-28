import io
import zipfile

import pytest


def test_missing_api_key_rejected(client, isolated_keys):
    r = client.post("/v1/generate", json={"text_lines": ["hi"]})
    assert r.status_code == 401


def test_invalid_api_key_rejected(client, isolated_keys):
    r = client.post("/v1/generate", json={"text_lines": ["hi"]}, headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_generate_returns_pdf(client, isolated_keys):
    r = client.post(
        "/v1/generate",
        json={"text_lines": ["hello"]},
        headers={"X-API-Key": "test-free-key"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_unknown_template_rejected(client, isolated_keys):
    r = client.post(
        "/v1/generate",
        json={"text_lines": ["hi"], "template": "not-a-template"},
        headers={"X-API-Key": "test-free-key"},
    )
    assert r.status_code == 400


def test_quota_enforced_per_key(client, isolated_keys):
    # test-free-key has quota_limit=3
    for _ in range(3):
        r = client.post("/v1/generate", json={"text_lines": ["x"]}, headers={"X-API-Key": "test-free-key"})
        assert r.status_code == 200

    r = client.post("/v1/generate", json={"text_lines": ["x"]}, headers={"X-API-Key": "test-free-key"})
    assert r.status_code == 402


def test_brand_profile_applied_without_override(client, isolated_keys, monkeypatch):
    captured = {}

    def fake_generate_pdf(path, text_lines, **kwargs):
        captured.update(kwargs)
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    import api.main as main_mod
    monkeypatch.setattr(main_mod, "generate_pdf", fake_generate_pdf)

    r = client.post("/v1/generate", json={"text_lines": ["hi"]}, headers={"X-API-Key": "test-brand-key"})
    assert r.status_code == 200
    assert captured["tab_fill_color"] == "#0B1F3A"
    assert captured["tab_text_color"] == "#FFFFFF"


def test_brand_profile_overridden_by_request(client, isolated_keys, monkeypatch):
    captured = {}

    def fake_generate_pdf(path, text_lines, **kwargs):
        captured.update(kwargs)
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    import api.main as main_mod
    monkeypatch.setattr(main_mod, "generate_pdf", fake_generate_pdf)

    r = client.post(
        "/v1/generate",
        json={"text_lines": ["hi"], "tab_fill_color": "#00FF00"},
        headers={"X-API-Key": "test-brand-key"},
    )
    assert r.status_code == 200
    assert captured["tab_fill_color"] == "#00FF00"
    assert captured["tab_text_color"] == "#FFFFFF"  # brand default still applies


def test_templates_listed(client, isolated_keys):
    r = client.get("/v1/templates")
    assert r.status_code == 200
    assert set(r.json()["templates"]) == {
        "note", "invoice", "certificate", "receipt", "memo", "worksheet",
    }


def test_batch_generates_one_pdf_per_row(client, isolated_keys):
    csv_content = (
        "filename,text\n"
        'row1,"line one\nline two"\n'
        "row2,line three\n"
    )
    files = {"file": ("roster.csv", csv_content, "text/csv")}
    r = client.post(
        "/v1/generate/batch",
        files=files,
        data={"template": "worksheet"},
        headers={"X-API-Key": "test-brand-key"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert set(z.namelist()) == {"row1.pdf", "row2.pdf"}


def test_batch_rejects_when_quota_insufficient_without_partial_charge(client, isolated_keys):
    csv_content = "filename,text\nrow1,a\nrow2,b\nrow3,c\nrow4,d\n"  # 4 rows, free key has quota 3
    files = {"file": ("roster.csv", csv_content, "text/csv")}
    r = client.post(
        "/v1/generate/batch",
        files=files,
        data={"template": "note"},
        headers={"X-API-Key": "test-free-key"},
    )
    assert r.status_code == 402

    # confirm nothing was charged: a 3-row batch should now succeed in full
    files2 = {"file": ("roster.csv", "filename,text\nrow1,a\nrow2,b\nrow3,c\n", "text/csv")}
    r2 = client.post(
        "/v1/generate/batch",
        files=files2,
        data={"template": "note"},
        headers={"X-API-Key": "test-free-key"},
    )
    assert r2.status_code == 200


def test_batch_rejects_missing_columns(client, isolated_keys):
    files = {"file": ("bad.csv", "a,b\n1,2\n", "text/csv")}
    r = client.post("/v1/generate/batch", files=files, headers={"X-API-Key": "test-free-key"})
    assert r.status_code == 400


def test_batch_sanitizes_path_traversal_filenames(client, isolated_keys):
    files = {"file": ("t.csv", "filename,text\n../../etc/evil,hi\n", "text/csv")}
    r = client.post("/v1/generate/batch", files=files, headers={"X-API-Key": "test-brand-key"})
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.namelist() == ["evil.pdf"]


def test_builder_ui_served(client, isolated_keys):
    r = client.get("/builder/builder.html")
    assert r.status_code == 200
    assert "Styled PDF Builder" in r.text


def test_root_redirects_to_builder(client, isolated_keys):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/builder/builder.html"
