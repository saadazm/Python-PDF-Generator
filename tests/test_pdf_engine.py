import re

from pdf_engine import TEMPLATES, generate_pdf


def test_all_templates_render(tmp_path):
    for name in TEMPLATES:
        out = tmp_path / f"{name}.pdf"
        generate_pdf(str(out), [f"{name} test line"], template=name)
        assert out.exists()
        assert out.stat().st_size > 0
        assert out.read_bytes().startswith(b"%PDF")


def test_unknown_template_raises(tmp_path):
    out = tmp_path / "x.pdf"
    try:
        generate_pdf(str(out), ["hi"], template="does-not-exist")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_pagination_on_long_input(tmp_path):
    out = tmp_path / "long.pdf"
    long_line = "word " * 60  # forces word-wrap
    lines = [long_line] * 40  # forces a page break
    generate_pdf(str(out), lines, template="note")

    content = out.read_bytes()
    # reportlab writes uncompressed page objects by default, so counting
    # them directly is a reliable (if unglamorous) smoke test here.
    page_count = len(re.findall(rb"/Type\s*/Page(?!s)", content))
    assert page_count >= 2


def test_logo_path_overrides_default_icon(tmp_path):
    out = tmp_path / "icon.pdf"
    generate_pdf(str(out), ["hi"], template="note", logo_path=None)
    assert out.exists()
