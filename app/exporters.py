"""Export the finished comic to a multi-page PDF using FPDF (fpdf2)."""
import os
from datetime import datetime

from fpdf import FPDF

from app import config

# Optional: drop DejaVuSans.ttf into static/fonts for full Unicode support.
FONT_PATH = config.FONTS_DIR / "DejaVuSans.ttf"
EXPORT_FOLDER = config.EXPORTS_DIR

_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
}


def _clean(text: str, unicode_font: bool) -> str:
    text = (text or "").replace("**", "").replace("__", "")
    if unicode_font:
        return text
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")  # core fonts are latin-1 only


def save_pdf(layout: list) -> str:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    unicode_font = FONT_PATH.exists()
    if unicode_font:
        pdf.add_font("DejaVu", "", str(FONT_PATH))
        family, italic = "DejaVu", ""
    else:
        family, italic = "Helvetica", "I"

    img_size = 130  # mm, panels are square

    for panel in layout:
        pdf.add_page()

        pdf.set_font(family, "", 16)
        pdf.multi_cell(
            0, 9, _clean(f"Panel {panel['panel']}: {panel['title']}", unicode_font),
            align="C", new_x="LMARGIN", new_y="NEXT",
        )

        y_image = pdf.get_y() + 3
        image_path = panel["image_path"]
        if os.path.exists(image_path):
            pdf.image(image_path, x=(pdf.w - img_size) / 2, y=y_image, w=img_size, h=img_size)
        else:
            pdf.set_y(y_image)
            pdf.set_font(family, "", 12)
            pdf.multi_cell(0, 8, f"Image missing: {image_path}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(y_image + img_size + 6)

        if panel.get("scene_description"):
            pdf.set_font(family, italic, 11)
            pdf.multi_cell(0, 6, _clean(panel["scene_description"], unicode_font),
                           new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        pdf.set_font(family, "", 12)
        pdf.multi_cell(0, 7, _clean(panel["text"], unicode_font), new_x="LMARGIN", new_y="NEXT")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_path = os.path.join(str(EXPORT_FOLDER), f"comic_{timestamp}.pdf")
    pdf.output(pdf_path)
    return pdf_path
