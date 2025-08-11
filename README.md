### **📄 Styled PDF Generator with Tab Label in Python**

This Python script uses **ReportLab** to generate a PDF with a **bordered content area** and a **custom tab-style label** embedded into the top border.
The tab contains an **icon** (in this example, `lightbulb.gif`) and styled text ("Note….."), making it ideal for **highlighting sections, headers, or annotations** in generated PDFs.

#### **Features**

* **Custom page border** with adjustable margins.
* **Tab-style header label** that visually “cuts” into the top border for a professional look.
* **Icon + text inside the tab** for branding or thematic emphasis.
* **Customizable colors, fonts, and sizes** for the tab and text.
* **Multi-line body text** inside the bordered area.

#### **How It Works**

1. Sets up **A4 page layout** using ReportLab.
2. Draws a **main rectangular border** for the content area.
3. “Masks” part of the border to embed the tab.
4. Draws a **rounded rectangle tab** with a background fill color.
5. Places an **image icon** next to the tab label text.
6. Writes body text lines inside the bordered area.
7. Saves the output as `generated.pdf` in the script’s folder.

#### **Requirements**

```bash
pip install reportlab
```

#### **Usage**

* Place your icon file (`lightbulb.gif` or any supported image format) in the same folder as the script.
* Run:

```bash
python pdf_tab_note.py
```

* The generated PDF will be saved in the same folder.

#### **Example Output**

* A clean **A4 PDF** with:

  * Light peach tab background (`#FFF0E9`)
  * Orange text color for the label (`#D38200`)
  * Black border around the content area
  * Example body text: `"Start....... "`


