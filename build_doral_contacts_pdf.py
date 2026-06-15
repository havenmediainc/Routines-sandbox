"""
Generate a clean PDF contact sheet: Doral FL Dental Offices — Phone & Email Directory
"""

import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

DARK_NAVY   = colors.HexColor("#0D1B2A")
ACCENT_BLUE = colors.HexColor("#1A6FAB")
LIGHT_GRAY  = colors.HexColor("#F4F6F8")
MID_GRAY    = colors.HexColor("#BDC3C7")
TEXT_DARK   = colors.HexColor("#2C3E50")
WHITE       = colors.white
ROW_ALT     = colors.HexColor("#EAF2FB")


def add_page_decor(canvas, doc):
    canvas.saveState()
    w, h = letter
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - 0.4 * inch, w, 0.4 * inch, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, 0, w, 0.3 * inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        w / 2, 0.1 * inch,
        f"Doral FL Dental Office Contact Directory  |  Page {doc.page}  |  June 2026  |  Haven Media Inc.",
    )
    canvas.restoreState()


def add_cover_page(canvas, doc):
    canvas.saveState()
    w, h = letter
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, h * 0.52, w, 6, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#1A5276"))
    canvas.rect(0, h * 0.52 - 6, w, 6, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#8FA3BF"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 0.3 * inch, "Confidential — Prepared by Haven Media Inc.")
    canvas.restoreState()


def load_contacts():
    with open("doral_dental_contacts.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_pdf():
    contacts = load_contacts()
    output = "doral_dental_contacts.pdf"

    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.5 * inch,
        title="Doral FL Dental Office Contact Directory",
        author="Haven Media Inc.",
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph("DORAL, FL", ParagraphStyle(
        "ct1", fontName="Helvetica-Bold", fontSize=16,
        textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Dental Offices", ParagraphStyle(
        "ct2", fontName="Helvetica-Bold", fontSize=34,
        leading=42, textColor=WHITE, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Phone &amp; Email Contact Directory", ParagraphStyle(
        "ct3", fontName="Helvetica-Bold", fontSize=18,
        leading=24, textColor=colors.HexColor("#B0C4DE"), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5 * inch))

    stats_data = [[
        Paragraph(f"<b>{len(contacts)}</b>\nPractices", ParagraphStyle(
            "s1", fontName="Helvetica-Bold", fontSize=16, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph(f"<b>{sum(1 for c in contacts if c['email'])}</b>\nEmails Confirmed", ParagraphStyle(
            "s2", fontName="Helvetica-Bold", fontSize=16, textColor=colors.HexColor("#5DADE2"), alignment=TA_CENTER)),
        Paragraph(f"<b>{len(contacts)}</b>\nPhone Numbers", ParagraphStyle(
            "s3", fontName="Helvetica-Bold", fontSize=16, textColor=colors.HexColor("#5DADE2"), alignment=TA_CENTER)),
    ]]
    stats_tbl = Table(stats_data, colWidths=[2 * inch] * 3)
    stats_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#162436")),
        ("BOX",           (0, 0), (-1, -1), 1, ACCENT_BLUE),
        ("LINEAFTER",     (0, 0), (1, -1), 0.5, ACCENT_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(stats_tbl)
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        "Researched: June 2026   |   Verified from practice websites, Yelp, and business directories",
        ParagraphStyle("cdate", fontName="Helvetica", fontSize=9,
                       textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Prepared by Haven Media Inc.",
        ParagraphStyle("cpre", fontName="Helvetica-Bold", fontSize=10,
                       textColor=colors.HexColor("#5DADE2"), alignment=TA_CENTER)))

    story.append(PageBreak())

    # ── CONTACT DIRECTORY TABLE ───────────────────────────────────────────────
    story.append(Paragraph("Contact Directory", ParagraphStyle(
        "h1", fontName="Helvetica-Bold", fontSize=14,
        textColor=DARK_NAVY, spaceAfter=4)))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceAfter=10))

    cell_style_label = ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=7.5,
                                       textColor=colors.HexColor("#7F8C8D"))
    cell_style_name  = ParagraphStyle("nm",  fontName="Helvetica-Bold", fontSize=9,
                                       textColor=DARK_NAVY, leading=12)
    cell_style_val   = ParagraphStyle("vl",  fontName="Helvetica", fontSize=8.5,
                                       textColor=TEXT_DARK, leading=12)
    cell_style_email = ParagraphStyle("em",  fontName="Helvetica", fontSize=8,
                                       textColor=ACCENT_BLUE, leading=11)
    cell_style_spec  = ParagraphStyle("sp",  fontName="Helvetica-Oblique", fontSize=7.5,
                                       textColor=colors.HexColor("#7F8C8D"), leading=10)

    # Header row
    header = [
        Paragraph("#", cell_style_label),
        Paragraph("Practice Name", cell_style_label),
        Paragraph("Phone", cell_style_label),
        Paragraph("Email", cell_style_label),
        Paragraph("Address", cell_style_label),
    ]
    rows = [header]

    for i, c in enumerate(contacts, 1):
        addr = f"{c['address']}, {c['city']}, {c['state']} {c['zip']}"
        email_text = c["email"] if c["email"] else "—  (contact via website)"
        rows.append([
            Paragraph(str(i), cell_style_val),
            Table(
                [[Paragraph(c["practice_name"], cell_style_name)],
                 [Paragraph(c["specialty"], cell_style_spec)]],
                colWidths=[2.55 * inch],
                style=TableStyle([
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                ]),
            ),
            Paragraph(c["phone"], cell_style_val),
            Paragraph(email_text, cell_style_email),
            Paragraph(addr, cell_style_val),
        ])

    col_w = [0.25*inch, 2.6*inch, 1.15*inch, 2.1*inch, 1.8*inch]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)

    style = [
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), DARK_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        # Borders
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, MID_GRAY),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
    ]
    tbl.setStyle(TableStyle(style))
    story.append(tbl)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "★  South Dental Doral does not list a public email address — contact via southdental.org contact form.",
        ParagraphStyle("fn", fontName="Helvetica-Oblique", fontSize=7.5,
                       textColor=colors.HexColor("#7F8C8D")),
    ))
    story.append(Paragraph(
        "★  Sage Dental Downtown Doral email shown is their credentialing address; use their website contact form for patient inquiries.",
        ParagraphStyle("fn2", fontName="Helvetica-Oblique", fontSize=7.5,
                       textColor=colors.HexColor("#7F8C8D")),
    ))

    doc.build(story, onFirstPage=add_cover_page, onLaterPages=add_page_decor)
    print(f"PDF saved to: {output}")


if __name__ == "__main__":
    build_pdf()
