from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
generated_pdf_path = os.path.join(script_dir, "generated.pdf")
icon_path = os.path.join(script_dir, "lightbulb.gif")  

def generate_pdf(file_path, text_lines):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4


    margin = 40                 # outer border margin
    tab_w, tab_h = 170, 28      # tab size
    tab_x = margin + 10         # tab left (shift from left border)
    tab_y = height - margin + 2 # tab baseline slightly above border
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.white)
    c.setLineWidth(0)
    c.rect(tab_x - 2, height - margin - 1, tab_w + 4, 6, stroke=0, fill=1)


    c.setFillColor(colors.HexColor("#FFF0E9"))  # soft blue fill
    c.setStrokeColor(colors.HexColor("#000000"))  # matching stroke
    c.setLineWidth(1.2)
    c.roundRect(tab_x, tab_y, tab_w, tab_h, 6, stroke=1, fill=1)

    pad_x = 10
    pad_y = 6

    icon_size = 20
    icon_x = tab_x + pad_x
    icon_y = tab_y + pad_y - 1 
    if os.path.exists(icon_path):
        c.drawImage(icon_path, icon_x, icon_y, width=icon_size, height=icon_size, mask='auto')


    c.setFillColor(colors.HexColor("#D38200"))
    c.setFont("Times-Bold", 15)
    text_x = icon_x + icon_size + 8
    text_y = tab_y + pad_y + 4
    c.drawString(text_x, text_y, "Note.....")


    c.setFillColor(colors.black)
    c.setFont("Times-Roman", 12)
    y = height - margin - 30
    for line in text_lines:
        c.drawString(margin + 12, y, line)
        y -= 18

    c.save()


generate_pdf(generated_pdf_path, [
    "Start....... ",
    
])
print(f"Generated PDF saved at: {generated_pdf_path}")
