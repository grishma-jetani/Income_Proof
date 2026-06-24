# data/synthetic_generator/render_pdf_phonepe.py
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import Image as RLImage


def render_phonepe_pdf(df, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm)
    
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    
    cell_style = ParagraphStyle(
        'PhonePeCell', 
        parent=normal_style, 
        fontSize=8, 
        leading=11, 
        textColor=colors.HexColor("#4a4a4a")
    )
    
    elements = []

    # --- 1. THE HEADER WITH PHONEPE LOGO ---
    header_style = ParagraphStyle('HeaderStyle', parent=normal_style, fontSize=12, leading=15)
    phone_number = "9847073579"
    date_range_str = f"{df['date'].min().strftime('%d %b, %Y')} - {df['date'].max().strftime('%d %b, %Y')}"
    header_text = f"<b>Transaction Statement for {phone_number}</b><br/><font color='#666666'>{date_range_str}</font>"

    # Check if user provided the logo, otherwise use a fallback string
    if os.path.exists("phonepe_logo.png"):
        pe_logo = RLImage("phonepe_logo.png", width=13*mm, height=12*mm)
        header_table = Table([[pe_logo, Paragraph(header_text, header_style)]], colWidths=[15*mm, 150*mm])
    else:
        header_table = Table([[Paragraph("<b>[Logo]</b>"), Paragraph(header_text, header_style)]], colWidths=[15*mm, 150*mm])
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('ALIGN', (0,0), (0,0), 'CENTER')
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 8 * mm))

    # --- 2. TABLE HEADER ---
    header_date = Paragraph("<b>Date</b>", cell_style)
    header_details = Paragraph("<b>Transaction Details</b>", cell_style)
    header_type = Paragraph("<b>Type</b>", cell_style)
    header_amount = Paragraph("<b>Amount</b>", cell_style)
    
    table_data = [[header_date, header_details, header_type, header_amount]]

    # --- 3. INLINE HDFC LOGO PREP ---
    # Setup the HTML image tag if the file exists
    if os.path.exists("boi_t_logo.png"):
        bank_icon_html = "<img src='boi_t_logo.png' width='8' height='8' valign='middle'/>"
    else:
        bank_icon_html = "[BOI]"

    for i, row in df.iterrows():
        time_str = "06:30 pm"
        
        raw_desc = row['description']
        merchant = raw_desc
        txn_id = f"T2026{100000 + i}"
        utr = f"3145{200000 + i}"
        
        if "-" in raw_desc:
            parts = raw_desc.split("-")
            if len(parts) >= 3:
                merchant = parts[1].replace('-', ' ')
                txn_id = parts[2].split('@')[0] if '@' in parts[2] else parts[2]

        if row['credit'] > 0:
            type_text = "<font color='#16a34a'><b>CREDIT</b></font>"
            amount_text = f"<font color='#16a34a'><b>₹{row['credit']:.0f}</b></font>"
            details_text = f"<b>Received from {merchant}</b><br/>Transaction ID {txn_id}<br/>UTR No {utr}<br/>Credited to {bank_icon_html} xxxxxxxx3131"
        else:
            type_text = "<b>DEBIT</b>"
            amount_text = f"<b>₹{row['debit']:.0f}</b>"
            details_text = f"<b>Paid to {merchant}</b><br/>Transaction ID {txn_id}<br/>UTR No {utr}<br/>Paid by {bank_icon_html} xxxxxxxx3131"

        date_text = f"<b>{row['date'].strftime('%b %d, %Y')}</b><br/><font color='#888888'>{time_str}</font>"

        table_data.append([
            Paragraph(date_text, cell_style),
            Paragraph(details_text, cell_style),
            Paragraph(type_text, cell_style),
            Paragraph(amount_text, cell_style)
        ])

    table = Table(table_data, colWidths=[35 * mm, 80 * mm, 30 * mm, 30 * mm])
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.transparent),
        ("BOX", (0, 0), (-1, -1), 0, colors.transparent),
    ]))
    
    elements.append(table)
    doc.build(elements)