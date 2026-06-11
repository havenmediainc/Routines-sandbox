"""
Generate a formatted PDF report: Naples FL Doctor Offices — Low Online Presence Leads
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import HRFlowable
from generate_csv import PRACTICES
from datetime import date

# ── Color palette ─────────────────────────────────────────────────────────────
DARK_NAVY   = colors.HexColor("#0D1B2A")
ACCENT_BLUE = colors.HexColor("#1A6FAB")
HIGH_RED    = colors.HexColor("#C0392B")
MED_ORANGE  = colors.HexColor("#E67E22")
LOW_GREEN   = colors.HexColor("#27AE60")
LIGHT_GRAY  = colors.HexColor("#F4F6F8")
MID_GRAY    = colors.HexColor("#BDC3C7")
TEXT_DARK   = colors.HexColor("#2C3E50")
WHITE       = colors.white

TIER_COLOR = {"HIGH": HIGH_RED, "MEDIUM": MED_ORANGE, "LOW": LOW_GREEN}
TIER_LABEL = {
    "HIGH":   "HIGH OPPORTUNITY",
    "MEDIUM": "MEDIUM OPPORTUNITY",
    "LOW":    "LOW OPPORTUNITY",
}

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_styles():
    s = {}
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=26,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName="Helvetica", fontSize=13,
        textColor=colors.HexColor("#B0C4DE"), alignment=TA_CENTER, spaceAfter=4,
    )
    s["cover_date"] = ParagraphStyle(
        "cover_date", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER,
    )
    s["section_header"] = ParagraphStyle(
        "section_header", fontName="Helvetica-Bold", fontSize=14,
        textColor=WHITE, alignment=TA_LEFT,
        leftIndent=6, spaceAfter=0,
    )
    s["card_name"] = ParagraphStyle(
        "card_name", fontName="Helvetica-Bold", fontSize=11,
        textColor=DARK_NAVY, spaceAfter=2,
    )
    s["card_doctor"] = ParagraphStyle(
        "card_doctor", fontName="Helvetica-Oblique", fontSize=9,
        textColor=ACCENT_BLUE, spaceAfter=3,
    )
    s["card_label"] = ParagraphStyle(
        "card_label", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.HexColor("#7F8C8D"),
    )
    s["card_value"] = ParagraphStyle(
        "card_value", fontName="Helvetica", fontSize=9,
        textColor=TEXT_DARK,
    )
    s["card_note"] = ParagraphStyle(
        "card_note", fontName="Helvetica-Oblique", fontSize=8,
        textColor=colors.HexColor("#555555"), spaceAfter=2,
    )
    s["card_opp"] = ParagraphStyle(
        "card_opp", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.HexColor("#1A6FAB"),
    )
    s["toc_item"] = ParagraphStyle(
        "toc_item", fontName="Helvetica", fontSize=9,
        textColor=TEXT_DARK, leftIndent=12,
    )
    s["footer"] = ParagraphStyle(
        "footer", fontName="Helvetica", fontSize=7,
        textColor=MID_GRAY, alignment=TA_CENTER,
    )
    s["intro_body"] = ParagraphStyle(
        "intro_body", fontName="Helvetica", fontSize=9.5,
        textColor=TEXT_DARK, leading=14, spaceAfter=6,
    )
    s["intro_bold"] = ParagraphStyle(
        "intro_bold", fontName="Helvetica-Bold", fontSize=9.5,
        textColor=DARK_NAVY, spaceAfter=4,
    )
    return s

ST = make_styles()


# ── Page template ─────────────────────────────────────────────────────────────

def add_page_decor(canvas, doc):
    canvas.saveState()
    w, h = letter
    # Top stripe
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - 0.4 * inch, w, 0.4 * inch, fill=1, stroke=0)
    # Bottom stripe
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, 0, w, 0.3 * inch, fill=1, stroke=0)
    # Footer text
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(w / 2, 0.1 * inch,
        f"Naples FL Doctor Office Lead Report  |  Page {doc.page}  |  Researched June 2026  |  Haven Media Inc.")
    canvas.restoreState()


def add_cover_page(canvas, doc):
    canvas.saveState()
    w, h = letter
    # Full dark background
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # Accent bar
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, h * 0.52, w, 6, fill=1, stroke=0)
    canvas.setFillColor(HIGH_RED)
    canvas.rect(0, h * 0.52 - 6, w, 6, fill=1, stroke=0)
    # Footer
    canvas.setFillColor(colors.HexColor("#8FA3BF"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 0.3 * inch, "Confidential — Prepared by Haven Media Inc.")
    canvas.restoreState()


# ── Helpers ───────────────────────────────────────────────────────────────────

def social_badge_text(practice):
    platforms = []
    for key, label in [
        ("has_facebook", "FB"), ("has_instagram", "IG"),
        ("has_twitter", "TW"), ("has_linkedin", "LI"),
        ("has_youtube", "YT"), ("has_tiktok", "TT"),
    ]:
        val = practice.get(key, False)
        if isinstance(val, str):
            val = val == "Yes"
        if val:
            platforms.append(label)
    if not platforms:
        return "None detected"
    return " · ".join(platforms)


def score_bar_cells(score):
    """Return a mini score visualization string."""
    filled = min(int(score / 10), 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar}  {score}/100"


def build_practice_card(p, tier_color):
    """Build a KeepTogether block for one practice."""
    elements = []

    name_para  = Paragraph(p["practice_name"], ST["card_name"])
    doc_para   = Paragraph(p["doctor_name"], ST["card_doctor"])
    spec_para  = Paragraph(f"<b>Specialty:</b> {p['specialty']}", ST["card_value"])

    phone  = p.get("phone", "") or "—"
    email  = p.get("email", "") or "—"
    addr   = f"{p['address']}, {p['city']}, {p['state']} {p['zip']}"
    web    = p.get("website", "") or "No website found"
    social = social_badge_text(p)
    score  = p.get("presence_score", 0)
    score_str = score_bar_cells(score)

    tier  = p["opportunity_tier"]
    t_col = tier_color.get(tier, ACCENT_BLUE)

    # Score + tier badge row
    badge_data = [[
        Paragraph(f"<b>{TIER_LABEL[tier]}</b>", ParagraphStyle(
            "badge", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)),
        Paragraph(f"Presence Score: {score}/100", ParagraphStyle(
            "score", fontName="Helvetica", fontSize=8, textColor=WHITE, alignment=TA_RIGHT)),
    ]]
    badge_tbl = Table(badge_data, colWidths=[3 * inch, 3.5 * inch])
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), t_col),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))

    # Contact info table
    contact_data = [
        [Paragraph("<b>Phone</b>", ST["card_label"]),    Paragraph(phone, ST["card_value"]),
         Paragraph("<b>Email</b>", ST["card_label"]),    Paragraph(email, ST["card_value"])],
        [Paragraph("<b>Address</b>", ST["card_label"]),  Paragraph(addr, ST["card_value"]),
         Paragraph("<b>Website</b>", ST["card_label"]),  Paragraph(web, ST["card_value"])],
        [Paragraph("<b>Social Media</b>", ST["card_label"]), Paragraph(social, ST["card_value"]),
         Paragraph("<b>Platforms</b>", ST["card_label"]),
         Paragraph(f"{p.get('social_platforms_count', 0)} active", ST["card_value"])],
    ]
    contact_tbl = Table(contact_data, colWidths=[0.9*inch, 2.6*inch, 0.9*inch, 2.1*inch])
    contact_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GRAY, WHITE]),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, MID_GRAY),
    ]))

    # Notes + opportunity
    notes_para = Paragraph(
        f"<b>Website Assessment:</b> {p.get('website_quality_notes', '')}",
        ST["card_note"]
    )
    opp_para = Paragraph(
        f"<b>★ Opportunity:</b> {p.get('key_opportunity', '')}",
        ST["card_opp"]
    )

    card_data = [[badge_tbl]]
    card_inner = Table([[name_para], [doc_para], [spec_para],
                        [Spacer(1, 3)],
                        [contact_tbl],
                        [Spacer(1, 3)],
                        [notes_para],
                        [opp_para]],
                       colWidths=[6.5 * inch])
    card_inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))

    outer = Table([[badge_tbl], [card_inner]], colWidths=[6.5 * inch])
    outer.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1, t_col),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    elements.append(KeepTogether([outer, Spacer(1, 10)]))
    return elements


# ── Summary table ─────────────────────────────────────────────────────────────

def build_summary_table(practices):
    headers = ["#", "Practice / Doctor", "Specialty", "Phone", "Tier", "Score", "Socials"]
    rows = [headers]

    sorted_p = sorted(
        practices,
        key=lambda x: (
            0 if x["opportunity_tier"] == "HIGH" else
            1 if x["opportunity_tier"] == "MEDIUM" else 2,
            x["presence_score"]
        )
    )

    for i, p in enumerate(sorted_p, 1):
        t = p["opportunity_tier"]
        rows.append([
            str(i),
            p["practice_name"][:38],
            p["specialty"][:28],
            p.get("phone", "—"),
            t,
            str(p.get("presence_score", 0)),
            str(p.get("social_platforms_count", 0)),
        ])

    col_w = [0.25*inch, 2.3*inch, 1.85*inch, 1.2*inch, 0.95*inch, 0.45*inch, 0.45*inch]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)

    style = [
        ("BACKGROUND",    (0, 0), (-1, 0), DARK_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("FONTSIZE",      (0, 1), (-1, -1), 7.5),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, MID_GRAY),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("ALIGN",         (5, 0), (6, -1), "CENTER"),
    ]

    # Color tier column
    for i, p in enumerate(sorted_p, 1):
        t = p["opportunity_tier"]
        c = TIER_COLOR[t]
        style.append(("TEXTCOLOR",  (4, i), (4, i), c))
        style.append(("FONTNAME",   (4, i), (4, i), "Helvetica-Bold"))

    tbl.setStyle(TableStyle(style))
    return tbl


# ── Main build ────────────────────────────────────────────────────────────────

def build_pdf():
    output = "naples_doctors_lead_report.pdf"
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.5 * inch,
        title="Naples FL Doctor Office Lead Report",
        author="Haven Media Inc.",
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("NAPLES, FL", ParagraphStyle(
        "ct1", fontName="Helvetica-Bold", fontSize=16,
        textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Doctor Offices", ParagraphStyle(
        "ct2", fontName="Helvetica-Bold", fontSize=32,
        leading=40, textColor=WHITE, alignment=TA_CENTER,
        spaceAfter=14)))
    story.append(Paragraph("Low Social Media &amp; Web Presence", ParagraphStyle(
        "ct3", fontName="Helvetica-Bold", fontSize=20,
        leading=26, textColor=colors.HexColor("#B0C4DE"), alignment=TA_CENTER,
        spaceAfter=6)))
    story.append(Spacer(1, 0.22 * inch))
    story.append(Paragraph("Lead Prospecting Report", ParagraphStyle(
        "ct4", fontName="Helvetica", fontSize=14,
        textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5 * inch))

    # Stats boxes on cover
    stats_data = [[
        Paragraph("<b>33</b>\nPractices\nResearched", ParagraphStyle(
            "s1", fontName="Helvetica-Bold", fontSize=14, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("<b>9</b>\nHIGH\nOpportunity", ParagraphStyle(
            "s2", fontName="Helvetica-Bold", fontSize=14, textColor=HIGH_RED, alignment=TA_CENTER)),
        Paragraph("<b>13</b>\nMEDIUM\nOpportunity", ParagraphStyle(
            "s3", fontName="Helvetica-Bold", fontSize=14, textColor=MED_ORANGE, alignment=TA_CENTER)),
        Paragraph("<b>11</b>\nLOW\nOpportunity", ParagraphStyle(
            "s4", fontName="Helvetica-Bold", fontSize=14, textColor=LOW_GREEN, alignment=TA_CENTER)),
    ]]
    stats_tbl = Table(stats_data, colWidths=[1.5 * inch] * 4)
    stats_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#162436")),
        ("BOX",           (0, 0), (-1, -1), 1, ACCENT_BLUE),
        ("LINEAFTER",     (0, 0), (2, -1),  0.5, ACCENT_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(stats_tbl)
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        f"Researched: June 2026   |   Prepared by Haven Media Inc.",
        ParagraphStyle("cdate", fontName="Helvetica", fontSize=10,
                       textColor=colors.HexColor("#8FA3BF"), alignment=TA_CENTER)))

    story.append(PageBreak())

    # ── HOW TO USE ────────────────────────────────────────────────────────────
    story.append(Paragraph("How to Use This Report", ParagraphStyle(
        "h1", fontName="Helvetica-Bold", fontSize=14,
        textColor=DARK_NAVY, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=10))

    intro_text = [
        ("Opportunity Tiers", True,
         "Each practice is assigned a tier based on its total digital presence score (0–100). "
         "Lower score = weaker online presence = bigger opportunity for your services."),
        (None, False,
         "<b><font color='#C0392B'>HIGH (score 0–19):</font></b>  Zero or near-zero social media. "
         "No website or basic/outdated site. Best candidates for a full digital build-out."),
        (None, False,
         "<b><font color='#E67E22'>MEDIUM (score 20–44):</font></b>  Facebook-only or one platform "
         "with very low engagement. Good candidates for social media expansion and website upgrades."),
        (None, False,
         "<b><font color='#27AE60'>LOW (score 45+):</font></b>  Already established online. "
         "Included for reference. Lower priority unless offering YouTube/TikTok strategy."),
        ("Scoring Breakdown", True,
         "Website present (+15) · Modern/SSL website (+5) · Facebook (+8) · Instagram (+8) · "
         "Twitter/X (+5) · LinkedIn (+4) · YouTube/TikTok (+5 each) · Contact form (+3) · Schema markup (+3)"),
        ("Data Sources", True,
         "NPI Registry, Yelp, Healthgrades, WebMD, US News Health, Collier County Medical Society, "
         "Facebook/Instagram/Twitter direct searches, individual practice websites. Researched June 2026."),
    ]

    for label, bold, text in intro_text:
        if label:
            story.append(Paragraph(label, ST["intro_bold"]))
        story.append(Paragraph(text, ST["intro_body"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))

    # ── SUMMARY TABLE ─────────────────────────────────────────────────────────
    story.append(Paragraph("All 33 Practices — Quick Reference", ParagraphStyle(
        "h1", fontName="Helvetica-Bold", fontSize=13,
        textColor=DARK_NAVY, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=10))
    story.append(build_summary_table(PRACTICES))
    story.append(PageBreak())

    # ── DETAIL CARDS BY TIER ─────────────────────────────────────────────────
    for tier, label, desc in [
        ("HIGH",   "HIGH OPPORTUNITY LEADS",
         "These practices have zero or near-zero digital presence. "
         "No social media detected across any platform. Most have no website or a severely outdated one. "
         "Best candidates for a complete digital marketing build-out."),
        ("MEDIUM", "MEDIUM OPPORTUNITY LEADS",
         "These practices have a minimal presence — typically Facebook-only or an account with almost no followers. "
         "Good candidates for social media expansion, Instagram setup, and website upgrades."),
        ("LOW",    "LOW OPPORTUNITY — FOR REFERENCE",
         "These practices have established digital presences and are included for competitive context. "
         "Lower priority unless pitching specific upgrades like TikTok, YouTube, or ad campaigns."),
    ]:
        tier_color = TIER_COLOR[tier]

        # Section header banner
        hdr_tbl = Table(
            [[Paragraph(label, ST["section_header"])]],
            colWidths=[6.5 * inch]
        )
        hdr_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), tier_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(hdr_tbl)
        story.append(Spacer(1, 4))
        story.append(Paragraph(desc, ParagraphStyle(
            "tier_desc", fontName="Helvetica-Oblique", fontSize=9,
            textColor=colors.HexColor("#555555"), spaceAfter=12,
        )))

        tier_practices = sorted(
            [p for p in PRACTICES if p["opportunity_tier"] == tier],
            key=lambda x: x["presence_score"]
        )

        for p in tier_practices:
            story.extend(build_practice_card(p, TIER_COLOR))

        if tier != "LOW":
            story.append(PageBreak())

    # Build
    doc.build(story, onFirstPage=add_cover_page, onLaterPages=add_page_decor)
    print(f"PDF generated: {output}")
    return output


if __name__ == "__main__":
    build_pdf()
