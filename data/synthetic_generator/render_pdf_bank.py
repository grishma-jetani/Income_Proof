# data/synthetic_generator/render_pdf_bank.py
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import Image as RLImage

def draw_watermark(canvas, doc):
    """Callback function to draw the background watermark on every page."""
    if os.path.exists("boi_watermark_2.png"):
        canvas.saveState()
        
        # Make the watermark roughly 140mm wide and tall
        img_width = 110 * mm
        img_height = 110 * mm
        
        # Center it on an A4 page (A4 is 210mm x 297mm)
        x_center = (210 * mm - img_width) / 2
        y_center = (297 * mm - img_height) / 2
        
        # mask='auto' respects the PNG's transparent background
        canvas.drawImage("boi_watermark_2.png", x_center, y_center, 
                         width=img_width, height=img_height, mask='auto')
        canvas.restoreState()


def render_bank_statement_pdf(df, output_path,
                               account_name="STUDENTS",
                               account_number="142310110006633"):
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=12 * mm, rightMargin=12 * mm)
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    elements = []

    # --- 1. BOI HEADER (Logo & Branch) ---
    if os.path.exists("boi_logo.png"):
        logo = RLImage("boi_logo.png", width=50*mm, height=16*mm)
        elements.append(Table([[logo]], colWidths=[186*mm], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    else:
        elements.append(Paragraph("<b>Bank of India</b>", styles["Title"]))
    
    elements.append(Paragraph("<b>Talawade Branch</b>", ParagraphStyle('Center', parent=normal_style, alignment=1)))
    elements.append(Spacer(1, 8 * mm))

    # --- 2. ACCOUNT DETAILS ---
    start_date = df['date'].min().strftime('%B %d, %Y')
    end_date = df['date'].max().strftime('%B %d, %Y')
    gen_date = df['date'].max().strftime('%d/%m/%Y')

    elements.append(Paragraph(f"<div align='right'>Date: {gen_date}</div>", normal_style))
    elements.append(Spacer(1, 4 * mm))

    account_info = [
        ["Name", f": {account_name}", "Account No", f": {account_number}"],
        ["Address", ": 00, GADRIYO KA MOHALLA", "Customer ID", ": 158707712"],
        ["", "  DIST CHITTORGARH", "Account Type", ": Savings Account"],
        ["Account Statement:", f"For the period {start_date} to {end_date}", "IFSC Code", ": BKID0001423"],
        ["", "", "MICR Code", ": 416013561"]
    ]
    
    info_table = Table(account_info, colWidths=[35*mm, 75*mm, 30*mm, 46*mm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10 * mm))

    # --- 3. BOI TRANSACTION TABLE ---
    table_data = [[
        "Sl No", "Txn Date", "Description", "Cheque No", 
        "Withdrawal\n(in Rs.)", "Deposits\n(in Rs.)", "Balance\n(in Rs.)"
    ]]

    for idx, row in df.iterrows():
        sl_no = str(idx + 1)
        date_str = row["date"].strftime("%d-%m-%Y")
        desc = row["description"].upper() 
        
        withdrawal = f"{row['debit']:,.2f}" if row["debit"] > 0 else ""
        deposit = f"{row['credit']:,.2f}" if row["credit"] > 0 else ""
        balance = f"{row['balance']:,.2f}"

        table_data.append([sl_no, date_str, desc, "", withdrawal, deposit, balance])

    boi_table = Table(table_data, colWidths=[12*mm, 20*mm, 60*mm, 18*mm, 24*mm, 24*mm, 28*mm])
    boi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cbe4f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
    ]))
    
    elements.append(boi_table)
    
    # --- 4. BUILD DOC WITH WATERMARK CALLBACK ---
    # We pass draw_watermark to run on every single page generated
    doc.build(elements, onFirstPage=draw_watermark, onLaterPages=draw_watermark)