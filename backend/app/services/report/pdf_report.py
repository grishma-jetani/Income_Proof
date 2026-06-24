import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colours ──────────────────────────────────────────────────────────
FOREST = colors.HexColor("#2D4A43")
GOLD = colors.HexColor("#C8A560")
CREAM = colors.HexColor("#FAF9F6")
RUST = colors.HexColor("#C2654A")
SAGE = colors.HexColor("#5B8A72")
LIGHT_BORDER = colors.HexColor("#E8E5DE")
INK = colors.HexColor("#1F2A27")
SLATE = colors.HexColor("#6B7280")


def build_income_report(
    transactions: list[dict],
    stability: dict,
    start_date: date,
    end_date: date,
    template_type: str = "loan",
    authenticity_signals_list: list[dict] | None = None,
) -> bytes:
    """
    Builds a PDF income report and returns raw bytes.
    template_type: 'loan' | 'rental'
    """
    stability = {
        **stability,
        "authenticity_signals_list": authenticity_signals_list or [],
    }

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "IPTitle",
        parent=styles["Normal"],
        fontSize=22,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        leading=28,
    )
    subtitle_style = ParagraphStyle(
        "IPSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#A8C5BD"),
        leading=14,
    )
    section_heading = ParagraphStyle(
        "IPSection",
        parent=styles["Normal"],
        fontSize=11,
        textColor=FOREST,
        fontName="Helvetica-Bold",
        spaceBefore=6,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "IPBody",
        parent=styles["Normal"],
        fontSize=9,
        textColor=INK,
        leading=14,
    )
    small_style = ParagraphStyle(
        "IPSmall",
        parent=styles["Normal"],
        fontSize=8,
        textColor=SLATE,
        leading=12,
    )
    disclaimer_style = ParagraphStyle(
        "IPDisclaimer",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=SLATE,
        leading=11,
    )

    elements = []

    # ── HEADER BANNER ──────────────────────────────────────────────────────
    template_label = (
        "Loan Application Report"
        if template_type == "loan"
        else "Rental Application Report"
    )
    header_data = [[
        Paragraph("IncomeProof", title_style),
        Paragraph(
            f"{template_label}<br/>"
            f"<font size='8'>"
            f"{start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')}"
            f"</font>",
            subtitle_style,
        ),
    ]]
    header_table = Table(header_data, colWidths=[90 * mm, 84 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FOREST),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, -1), 8 * mm),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 6 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6 * mm),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8 * mm))

    # ── SUMMARY TILES ──────────────────────────────────────────────────────
    total_income = sum(float(t.get("credit", 0)) for t in transactions)
    total_expenses = sum(float(t.get("debit", 0)) for t in transactions)
    net_savings = total_income - total_expenses
    score = stability.get("stability_score", 0)

    def tile(label, value, value_color=INK):
        return [Paragraph(
            f"<font size='7' color='#6B7280'>{label}</font><br/>"
            f"<font size='13' color='{value_color}'><b>{value}</b></font>",
            body_style,
        )]

    summary_data = [[
        tile("Total Income", f"Rs {total_income:,.0f}"),
        tile("Total Expenses", f"Rs {total_expenses:,.0f}", "#C2654A"),
        tile("Net Savings", f"Rs {net_savings:,.0f}", "#5B8A72"),
        tile("Stability Score", f"{score:.0f} / 100", "#C8A560"),
    ]]
    summary_table = Table(summary_data, colWidths=[43.5 * mm] * 4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    # ── STABILITY EXPLANATION ──────────────────────────────────────────────
    elements.append(Paragraph("Income Stability Analysis", section_heading))
    elements.append(
        HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
    )
    elements.append(Paragraph(stability.get("explanation", ""), body_style))

    if stability.get("action_tip"):
        elements.append(Spacer(1, 3 * mm))
        tip_data = [[
            Paragraph(f"💡  {stability['action_tip']}", body_style)
        ]]
        tip_table = Table(tip_data, colWidths=[174 * mm])
        tip_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF7EE")),
            ("BOX", (0, 0), (-1, -1), 0.5, GOLD),
            ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        elements.append(tip_table)

    elements.append(Spacer(1, 6 * mm))

    # ── STATEMENT VERIFICATION SUMMARY ────────────────────────────────────
    auth_signals = stability.get("authenticity_signals_list", [])
    if auth_signals:
        elements.append(Paragraph("Statement Verification", section_heading))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
        )

        SIGNAL_COLORS = {
            "verified": "#5B8A72",
            "suspicious": "#C2654A",
            "unverified": "#C8A560",
            "inconclusive": "#9CA3AF",
        }
        SIGNAL_ICONS = {
            "verified": "OK",
            "suspicious": "WARNING",
            "unverified": "CHECK",
            "inconclusive": "UNKNOWN",
        }
        CHECK_LABELS = {
            "producer_metadata": "PDF Producer",
            "modification_date": "Modified After Creation",
            "font_consistency": "Font Consistency",
            "text_layer": "Text Layer Coverage",
        }

        for auth in auth_signals:
            signal = auth.get("overall_signal", "inconclusive")
            color_hex = SIGNAL_COLORS.get(signal, "#9CA3AF")
            signal_label = SIGNAL_ICONS.get(signal, "UNKNOWN")
            filename = auth.get("filename", "Statement")
            explanation = auth.get("overall_explanation", "")

            auth_row_data = [[Paragraph(
                f"<font color='{color_hex}'><b>[{signal_label}] {filename}</b></font><br/>"
                f"<font size='8' color='#6B7280'>{explanation}</font>",
                body_style,
            )]]
            auth_row = Table(auth_row_data, colWidths=[174 * mm])
            auth_row.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAF8")),
                ("BOX", (0, 0), (-1, -1), 0.4, LIGHT_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]))
            elements.append(auth_row)
            elements.append(Spacer(1, 2 * mm))

            if auth.get("checks"):
                check_data = [["Check", "Result", "Detail"]]
                for chk in auth["checks"]:
                    result_label = (
                        "PASS" if chk["passed"] is True
                        else "FAIL" if chk["passed"] is False
                        else "N/A"
                    )
                    check_data.append([
                        CHECK_LABELS.get(chk["check"], chk["check"]),
                        result_label,
                        Paragraph(
                            (chk.get("detail") or "")[:120], small_style
                        ),
                    ])
                chk_table = Table(
                    check_data, colWidths=[42 * mm, 14 * mm, 118 * mm]
                )
                chk_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F0EE")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
                    ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                elements.append(chk_table)
                elements.append(Spacer(1, 3 * mm))

            # ── NEW: CROSS-SOURCE OVERLAP WARNING BOX ──────────────────────
            if auth.get("has_cross_source_overlap") and auth.get("overlap_details"):
                overlap = auth["overlap_details"]
                if overlap.get("conflicts"):
                    conflict_texts = []
                    for c in overlap["conflicts"]:
                        # Extract the exact risk detail
                        text = f"<b>{overlap.get('new_source', 'This source')}</b> overlaps with <b>{c.get('existing_source')}</b> during {c.get('overlap_range')}. {c.get('risk')}"
                        conflict_texts.append(text)
                    
                    overlap_data = [[
                        Paragraph(
                            f"<font color='#C8A560'><b>⚠️ Cross-Source Overlap Detected</b></font><br/>"
                            f"<font size='8' color='#6B7280'>{'<br/>'.join(conflict_texts)}<br/><br/><i>Note: Income in this period may be double-counted. Please review amounts carefully.</i></font>",
                            body_style,
                        )
                    ]]
                    overlap_table = Table(overlap_data, colWidths=[174 * mm])
                    overlap_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF9F0")), # Light gold background
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2C68A")), # Gold border
                        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                    ]))
                    elements.append(overlap_table)
                    elements.append(Spacer(1, 3 * mm))

    elements.append(Spacer(1, 3 * mm))

    # ── PLATFORM BREAKDOWN ─────────────────────────────────────────────────
    platform_breakdown = stability.get("platform_breakdown", {})
    sorted_platforms = sorted(
        platform_breakdown.items(), key=lambda x: x[1], reverse=True
    )

    if platform_breakdown:
        elements.append(Paragraph("Income by Platform", section_heading))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
        )

        pct_total = sum(v for _, v in sorted_platforms)
        plat_data = [["Platform", "Total Earned", "Share of Income"]]
        for plat, amt in sorted_platforms:
            pct = (amt / pct_total * 100) if pct_total > 0 else 0
            plat_data.append([plat, f"Rs {amt:,.0f}", f"{pct:.1f}%"])

        plat_table = Table(plat_data, colWidths=[80 * mm, 50 * mm, 44 * mm])
        plat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), FOREST),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]))
        elements.append(plat_table)
        elements.append(Spacer(1, 6 * mm))

    # ── TEMPLATE-SPECIFIC SECTION ──────────────────────────────────────────
    primary_platform = sorted_platforms[0][0] if sorted_platforms else "N/A"
    mean_monthly = stability.get("mean_weekly_income", 0) * 4.33

    if template_type == "loan":
        elements.append(Paragraph("Lender Summary", section_heading))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
        )
        factor_detail = stability.get("_factor_detail") or stability.get("factor_detail") or {}
        trend_dir = (
            factor_detail.get("factor_meta", {})
            .get("trend_momentum", {})
            .get("trend_direction", "flat")
        )
        cv_pct = stability.get("cv_pct", 0)
        loan_rows = [
            ["Average Monthly Income (estimated)", f"Rs {mean_monthly:,.0f}"],
            ["Income Stability Score", f"{score:.0f} / 100"],
            ["Score Band", factor_detail.get("score_band", "—")],
            ["Income Variation (CV)", f"{cv_pct:.1f}%"],
            ["Trend Direction", trend_dir.capitalize()],
            ["Primary Income Source", primary_platform],
            ["Statement Period",
             f"{start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')}"],
        ]
        loan_table = Table(loan_rows, colWidths=[100 * mm, 74 * mm])
        loan_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_BORDER),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CREAM, colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]))
        elements.append(loan_table)
    else:
        elements.append(Paragraph("Rental Application Summary", section_heading))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
        )
        days_in_period = max((end_date - start_date).days, 1)
        monthly_savings = net_savings / (days_in_period / 30)
        rent_rows = [
            ["Estimated Monthly Income", f"Rs {mean_monthly:,.0f}"],
            ["Estimated Monthly Savings", f"Rs {monthly_savings:,.0f}"],
            ["Income Stability Score", f"{score:.0f} / 100"],
            ["Total Income in Period", f"Rs {total_income:,.0f}"],
            ["Primary Income Source", primary_platform],
        ]
        rent_table = Table(rent_rows, colWidths=[100 * mm, 74 * mm])
        rent_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_BORDER),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CREAM, colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]))
        elements.append(rent_table)

    elements.append(Spacer(1, 8 * mm))

    # ── FIVE-FACTOR SCORE BREAKDOWN ────────────────────────────────────────
    factor_detail = (
        stability.get("_factor_detail")
        or stability.get("factor_detail")
        or {}
    )
    factor_scores = factor_detail.get("factor_scores", {})
    factor_meta = factor_detail.get("factor_meta", {})
    score_band = factor_detail.get("score_band", "—")
    num_weeks = factor_detail.get("num_weeks_analysed", "—")

    if factor_scores:
        elements.append(Paragraph("Income Stability — Score Breakdown", section_heading))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
        )

        FACTOR_DISPLAY = {
            "regularity":          ("Income Regularity",           "30%", "MAD/median Robust CV"),
            "income_floor":        ("Income Floor",                "25%", "P25/median ratio"),
            "trend_momentum":      ("Trend Momentum",              "20%", "OLS slope × R²"),
            "concentration_risk":  ("Platform Concentration Risk", "15%", "Inverted HHI (experimental)"),
            "consistency_rate":    ("Income Consistency Rate",     "10%", "Weeks-with-income ratio"),
        }

        # Header row
        breakdown_data = [["Factor", "Weight", "Score /100", "Method", "Interpretation"]]

        for key, (label, weight, method) in FACTOR_DISPLAY.items():
            fscore = factor_scores.get(key, None)
            if fscore is None:
                continue
            interp = (
                factor_meta.get(key, {}).get("interpretation", "")
                or ""
            )[:80]
            breakdown_data.append([
                label,
                weight,
                f"{fscore:.0f}",
                method,
                Paragraph(interp, small_style),
            ])

        # Weighted total row
        weights_map = factor_detail.get("weights", {})
        weighted_total = sum(
            factor_scores.get(k, 0) * w for k, w in weights_map.items()
        )
        breakdown_data.append([
            "COMPOSITE SCORE",
            "100%",
            f"{weighted_total:.0f}  [{score_band}]",
            "",
            Paragraph(
                f"{num_weeks} weeks analysed · "
                "Scaling constants are design priors, not empirically calibrated.",
                small_style,
            ),
        ])

        bd_table = Table(
            breakdown_data,
            colWidths=[42 * mm, 12 * mm, 20 * mm, 38 * mm, 62 * mm],
        )
        bd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), FOREST),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # Last row (composite) — highlight
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FBF7EE")),
            ("FONTNAME", (0, -1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, CREAM]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
            ("ALIGN", (1, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(bd_table)

        # Income adequacy note if applicable
        adequacy = factor_detail.get("adequacy_note")
        if adequacy:
            elements.append(Spacer(1, 2 * mm))
            note_data = [[Paragraph(f"⚠  {adequacy}", small_style)]]
            note_table = Table(note_data, colWidths=[174 * mm])
            note_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3F0")),
                ("BOX", (0, 0), (-1, -1), 0.5, RUST),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]))
            elements.append(note_table)

        elements.append(Spacer(1, 6 * mm))

    # ── RECENT INCOME TRANSACTIONS ─────────────────────────────────────────
    elements.append(
        Paragraph("Transaction Detail (Recent 20 Income)", section_heading)
    )
    elements.append(
        HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER, spaceAfter=4)
    )

    income_txns = sorted(
        [t for t in transactions if float(t.get("credit", 0)) > 0],
        key=lambda x: x["txn_date"],
        reverse=True,
    )[:20]

    txn_data = [["Date", "Description", "Category", "Amount"]]
    for t in income_txns:
        txn_data.append([
            str(t["txn_date"]),
            Paragraph(t["description"][:55], small_style),
            t.get("category", "—"),
            f"Rs {float(t['credit']):,.0f}",
        ])

    txn_table = Table(txn_data, colWidths=[22 * mm, 72 * mm, 45 * mm, 35 * mm])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(txn_table)
    elements.append(Spacer(1, 10 * mm))

    # ── FOOTER DISCLAIMER ─────────────────────────────────────────────────
    elements.append(
        HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER)
    )
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        "This report was generated by IncomeProof and is based solely on "
        "transaction data provided by the applicant. It is intended as a "
        "financial identity summary for informal review and does not constitute "
        "a certified income statement. The income stability score uses a "
        "multi-factor model whose scaling constants are design priors pending "
        "calibration against loan repayment outcome data. Lenders and landlords "
        "should use this report alongside other verification methods as appropriate.",
        disclaimer_style,
    ))

    doc.build(elements)
    return buffer.getvalue()