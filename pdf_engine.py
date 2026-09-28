"""Reusable, parameterized engine for the tab-style bordered PDF note.

generatepdf.py is a thin CLI wrapper around this module; api/main.py wraps
it as an HTTP service. Both call generate_pdf() so the rendering logic
lives in exactly one place.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
import os

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

# Each template is a named color/font preset. "icon" is a filename resolved
# against ASSETS_DIR; templates without a bundled icon simply omit one
# unless the caller (or a white-label brand profile) supplies icon_path/logo_path.
TEMPLATES = {
    "note": {
        "tab_text": "Note.....",
        "tab_fill_color": "#FFF0E9",
        "tab_text_color": "#D38200",
        "tab_font": "Times-Bold",
        "body_font": "Times-Roman",
        "icon": "lightbulb.gif",
    },
    "invoice": {
        "tab_text": "Invoice",
        "tab_fill_color": "#E9F0FF",
        "tab_text_color": "#1F4FD8",
        "tab_font": "Helvetica-Bold",
        "body_font": "Helvetica",
        "icon": None,
    },
    "certificate": {
        "tab_text": "Certificate",
        "tab_fill_color": "#FFF7DC",
        "tab_text_color": "#A67C00",
        "tab_font": "Times-Bold",
        "body_font": "Times-Roman",
        "icon": None,
    },
    "receipt": {
        "tab_text": "Receipt",
        "tab_fill_color": "#E9FFF0",
        "tab_text_color": "#1F8A4C",
        "tab_font": "Helvetica-Bold",
        "body_font": "Helvetica",
        "icon": None,
    },
    "memo": {
        "tab_text": "Memo",
        "tab_fill_color": "#F0E9FF",
        "tab_text_color": "#6B21D8",
        "tab_font": "Times-Bold",
        "body_font": "Times-Roman",
        "icon": None,
    },
    "worksheet": {
        "tab_text": "Worksheet",
        "tab_fill_color": "#E9FFFC",
        "tab_text_color": "#0E8A7D",
        "tab_font": "Times-Bold",
        "body_font": "Times-Roman",
        "icon": None,
    },
}

BODY_FONT_SIZE = 12
LINE_HEIGHT = 18


def _wrap_line(line, font_name, font_size, max_width):
    """Greedy word-wrap a single line to fit within max_width."""
    if not line:
        return [""]

    words = line.split(" ")
    wrapped, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                wrapped.append(current)
            current = word
    if current:
        wrapped.append(current)
    return wrapped or [""]


def _draw_frame(c, width, height, margin, tab_text, tab_fill_color, tab_text_color, tab_font, icon_path):
    """Draws the bordered content area and the tab-style header label."""
    tab_w, tab_h = 170, 28      # tab size
    tab_x = margin + 10         # tab left (shift from left border)
    tab_y = height - margin + 2 # tab baseline slightly above border

    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    c.setFillColor(colors.white)
    c.setStrokeColor(colors.white)
    c.setLineWidth(0)
    c.rect(tab_x - 2, height - margin - 1, tab_w + 4, 6, stroke=0, fill=1)

    c.setFillColor(colors.HexColor(tab_fill_color))
    c.setStrokeColor(colors.HexColor("#000000"))
    c.setLineWidth(1.2)
    c.roundRect(tab_x, tab_y, tab_w, tab_h, 6, stroke=1, fill=1)

    pad_x = 10
    pad_y = 6

    icon_size = 20
    icon_x = tab_x + pad_x
    icon_y = tab_y + pad_y - 1
    text_x = tab_x + pad_x
    if icon_path and os.path.exists(icon_path):
        c.drawImage(icon_path, icon_x, icon_y, width=icon_size, height=icon_size, mask='auto')
        text_x = icon_x + icon_size + 8

    c.setFillColor(colors.HexColor(tab_text_color))
    c.setFont(tab_font, 15)
    text_y = tab_y + pad_y + 4
    c.drawString(text_x, text_y, tab_text)


def generate_pdf(
    file_path,
    text_lines,
    template="note",
    tab_text=None,
    tab_fill_color=None,
    tab_text_color=None,
    tab_font=None,
    body_font=None,
    body_font_size=BODY_FONT_SIZE,
    icon_path=None,
    logo_path=None,
    margin=40,
):
    """Render text_lines into a bordered, tab-labeled PDF at file_path.

    template selects a color/font preset from TEMPLATES; any of the
    tab_*/body_font kwargs override that preset. logo_path (white-label
    branding) takes priority over icon_path, which takes priority over the
    template's bundled icon.
    """
    if template not in TEMPLATES:
        raise ValueError(f"Unknown template {template!r}; choose one of {sorted(TEMPLATES)}")
    preset = TEMPLATES[template]

    tab_text = tab_text if tab_text is not None else preset["tab_text"]
    tab_fill_color = tab_fill_color or preset["tab_fill_color"]
    tab_text_color = tab_text_color or preset["tab_text_color"]
    tab_font = tab_font or preset["tab_font"]
    body_font = body_font or preset["body_font"]

    resolved_icon = logo_path or icon_path
    if resolved_icon is None and preset["icon"]:
        resolved_icon = os.path.join(ASSETS_DIR, preset["icon"])

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    max_text_width = width - 2 * margin - 24

    def new_page():
        _draw_frame(c, width, height, margin, tab_text, tab_fill_color, tab_text_color, tab_font, resolved_icon)
        c.setFillColor(colors.black)
        c.setFont(body_font, body_font_size)
        return height - margin - 30

    y = new_page()

    for line in text_lines:
        for wrapped_line in _wrap_line(line, body_font, body_font_size, max_text_width):
            if y < margin + LINE_HEIGHT:
                c.showPage()
                y = new_page()
            c.drawString(margin + 12, y, wrapped_line)
            y -= LINE_HEIGHT

    c.save()
