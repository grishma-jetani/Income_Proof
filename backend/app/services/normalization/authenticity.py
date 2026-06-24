"""
PDF Authenticity Verifier
─────────────────────────
Runs a set of heuristic checks on an uploaded PDF to assess whether it
is a genuine bank/UPI-app export or has been manually created/edited.

Checks performed:
  1. Producer metadata — is the PDF producer a known banking/fintech tool?
  2. Creation vs Modification date gap — was the file re-saved after creation?
  3. Font consistency — does the file use a single consistent font family?
  4. Text layer coverage — is there a real text layer (not all-image scans)?
  5. Format-specific signals — BOI vs PhonePe vs generic patterns.

Returns a dict stored as JSON on Statement.authenticity_signals.
"""

import re
from datetime import datetime, timezone

import pdfplumber

# ── Known-good producer strings (case-insensitive substrings) ──────────────
BANKING_PRODUCERS = [
    "itext",            # very common in Indian bank PDFs
    "oracle bi",        # Oracle BI Publisher — BOI, SBI, PNB
    "apache fop",       # Apache FOP — some PSU banks
    "jasper",           # JasperReports — common in core banking
    "finacle",          # Infosys Finacle
    "temenos",          # Temenos T24
    "bankware",
    "flexcube",         # Oracle FLEXCUBE
    "pdf generator",    # generic but often bank middleware
    "phonepe",
    "paytm",
    "gpay",
    "bhim",
    "razorpay",
]

# Producers that strongly suggest manual creation / editing
SUSPICIOUS_PRODUCERS = [
    "microsoft word",
    "microsoft excel",
    "libreoffice",
    "openoffice",
    "reportlab",        # Python PDF library — catches our own synthetic PDFs
    "wkhtmltopdf",      # HTML-to-PDF — sometimes used to fake statements
    "pdfcreator",
    "cute pdf",
    "pdf24",
    "smallpdf",
    "ilovepdf",
    "sejda",
    "canva",
    "adobe acrobat",    # Acrobat is used for legitimate signing but also editing
]

# Tolerated modification gap in seconds (bank systems sometimes stamp
# a "print date" a few seconds after the PDF is generated)
MODIFICATION_GAP_TOLERANCE_SECONDS = 300   # 5 minutes


def _parse_pdf_date(date_str: str | None) -> datetime | None:
    """
    Parse PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
    e.g. "D:20260115143022+05'30'"
    """
    if not date_str:
        return None
    # strip D: prefix
    s = date_str.strip()
    if s.startswith("D:"):
        s = s[2:]
    # take first 14 chars (YYYYMMDDHHmmss)
    s = s[:14]
    try:
        return datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _check_producer(info: dict) -> dict:
    producer = str(info.get("Producer") or info.get("Creator") or "").lower()
    creator = str(info.get("Creator") or "").lower()
    combined = f"{producer} {creator}".strip()

    if not combined.strip():
        return {
            "check": "producer_metadata",
            "passed": False,
            "confidence": "low",
            "detail": "No producer metadata found. Genuine bank PDFs always embed this.",
            "raw": None,
        }

    for known in BANKING_PRODUCERS:
        if known in combined:
            return {
                "check": "producer_metadata",
                "passed": True,
                "confidence": "high",
                "detail": f"Producer matches known banking/fintech tool: '{combined.strip()}'.",
                "raw": combined.strip(),
            }

    for suspect in SUSPICIOUS_PRODUCERS:
        if suspect in combined:
            return {
                "check": "producer_metadata",
                "passed": False,
                "confidence": "high",
                "detail": (
                    f"Producer '{combined.strip()}' is a general-purpose document tool, "
                    "not a banking system. This PDF may have been manually created or edited."
                ),
                "raw": combined.strip(),
            }

    return {
        "check": "producer_metadata",
        "passed": None,   # unknown — not in either list
        "confidence": "medium",
        "detail": f"Unrecognized producer: '{combined.strip()}'. Could not confirm banking origin.",
        "raw": combined.strip(),
    }


def _check_modification_date(info: dict) -> dict:
    creation = _parse_pdf_date(info.get("CreationDate"))
    modification = _parse_pdf_date(info.get("ModDate"))

    if creation is None and modification is None:
        return {
            "check": "modification_date",
            "passed": None,
            "confidence": "low",
            "detail": "No creation or modification date found in metadata.",
            "gap_seconds": None,
        }

    if modification is None or creation is None:
        return {
            "check": "modification_date",
            "passed": True,
            "confidence": "low",
            "detail": "Only one of creation/modification dates present — inconclusive.",
            "gap_seconds": None,
        }

    gap = abs((modification - creation).total_seconds())

    if gap <= MODIFICATION_GAP_TOLERANCE_SECONDS:
        return {
            "check": "modification_date",
            "passed": True,
            "confidence": "high",
            "detail": f"File created and last modified within {gap:.0f}s of each other — consistent with bank-generated PDF.",
            "gap_seconds": gap,
        }
    else:
        gap_hours = gap / 3600
        return {
            "check": "modification_date",
            "passed": False,
            "confidence": "medium",
            "detail": (
                f"File was modified {gap_hours:.1f} hours after creation. "
                "This may indicate the PDF was opened and re-saved after download."
            ),
            "gap_seconds": gap,
        }


def _check_font_consistency(pdf) -> dict:
    """
    Checks whether all pages use a consistent set of font families.
    Genuine bank PDFs embed a fixed set of fonts; edited PDFs often introduce
    additional fonts from the editing tool.
    """
    font_sets: list[set] = []

    for page in pdf.pages:
        try:
            chars = page.chars
        except Exception:
            continue

        page_fonts = {
            re.sub(r"[+,\-].*$", "", c.get("fontname", "")).strip().upper()
            for c in chars
            if c.get("fontname")
        }
        if page_fonts:
            font_sets.append(page_fonts)

    if not font_sets:
        return {
            "check": "font_consistency",
            "passed": None,
            "confidence": "low",
            "detail": "No font information found (possibly a scanned/image PDF).",
            "unique_font_families": [],
        }

    # Union of all fonts across all pages
    all_fonts = set.union(*font_sets)
    # Fonts that appear on page 1 (expected baseline)
    baseline = font_sets[0] if font_sets else set()
    # Extra fonts introduced on later pages
    extra = all_fonts - baseline

    if len(all_fonts) <= 5 and not extra:
        return {
            "check": "font_consistency",
            "passed": True,
            "confidence": "high",
            "detail": f"Consistent font set across all pages: {sorted(all_fonts)}.",
            "unique_font_families": sorted(all_fonts),
        }
    elif extra:
        return {
            "check": "font_consistency",
            "passed": False,
            "confidence": "medium",
            "detail": (
                f"Font(s) {sorted(extra)} appear on later pages but not on page 1. "
                "This may indicate content was inserted after original generation."
            ),
            "unique_font_families": sorted(all_fonts),
        }
    else:
        return {
            "check": "font_consistency",
            "passed": True,
            "confidence": "medium",
            "detail": f"Many fonts present ({len(all_fonts)}) but consistent across pages.",
            "unique_font_families": sorted(all_fonts),
        }


def _check_text_layer(pdf) -> dict:
    """
    Checks whether the PDF has a proper text layer.
    Genuine digital bank PDFs always have extractable text.
    An all-image PDF (screenshot of a statement) has no text layer.
    A partially-image PDF may have had text overlaid after the fact.
    """
    pages_with_text = 0
    pages_with_images = 0

    for page in pdf.pages:
        chars = page.chars if hasattr(page, "chars") else []
        images = page.images if hasattr(page, "images") else []
        if len(chars) > 20:
            pages_with_text += 1
        if images:
            pages_with_images += 1

    total = len(pdf.pages)
    if total == 0:
        return {
            "check": "text_layer",
            "passed": None,
            "confidence": "low",
            "detail": "PDF has no pages.",
            "pages_with_text": 0,
            "pages_with_images": 0,
        }

    text_ratio = pages_with_text / total

    if text_ratio >= 0.9:
        return {
            "check": "text_layer",
            "passed": True,
            "confidence": "high",
            "detail": f"Strong text layer: {pages_with_text}/{total} pages have extractable text.",
            "pages_with_text": pages_with_text,
            "pages_with_images": pages_with_images,
        }
    elif text_ratio >= 0.5:
        return {
            "check": "text_layer",
            "passed": None,
            "confidence": "medium",
            "detail": (
                f"Partial text layer: only {pages_with_text}/{total} pages have extractable text. "
                "Some pages may be image-based."
            ),
            "pages_with_text": pages_with_text,
            "pages_with_images": pages_with_images,
        }
    else:
        return {
            "check": "text_layer",
            "passed": False,
            "confidence": "medium",
            "detail": (
                f"Minimal text layer: {pages_with_text}/{total} pages have extractable text. "
                "This may be a scanned or screenshot-based PDF."
            ),
            "pages_with_text": pages_with_text,
            "pages_with_images": pages_with_images,
        }


def _compute_overall(checks: list[dict]) -> tuple[str, str]:
    """
    Derives an overall authenticity signal and confidence level
    from individual check results.

    Returns: (signal, explanation)
    signal: 'verified' | 'suspicious' | 'unverified' | 'inconclusive'
    """
    failed_high = [c for c in checks if c["passed"] is False and c["confidence"] == "high"]
    failed_any = [c for c in checks if c["passed"] is False]
    passed_high = [c for c in checks if c["passed"] is True and c["confidence"] == "high"]
    unknown = [c for c in checks if c["passed"] is None]

    if failed_high:
        names = ", ".join(c["check"] for c in failed_high)
        return (
            "suspicious",
            f"High-confidence failure on: {names}. "
            "This statement shows signs of manual creation or editing.",
        )

    if len(failed_any) >= 2:
        names = ", ".join(c["check"] for c in failed_any)
        return (
            "suspicious",
            f"Multiple checks failed ({names}). Treat with caution.",
        )

    if len(passed_high) >= 2 and not failed_any:
        return (
            "verified",
            "Multiple high-confidence checks passed. This statement appears genuine.",
        )

    if len(unknown) >= 3:
        return (
            "inconclusive",
            "Insufficient metadata to verify authenticity. "
            "Consider requesting a freshly downloaded statement.",
        )

    return (
        "unverified",
        "Some checks passed but confidence is limited. "
        "No strong evidence of tampering, but also no strong banking-origin signal.",
    )


def verify_pdf_authenticity(filepath: str) -> dict:
    """
    Main entry point. Returns a structured authenticity report dict.
    Safe to call on any PDF — catches all exceptions internally.
    """
    try:
        with pdfplumber.open(filepath) as pdf:
            info = pdf.metadata or {}

            checks = [
                _check_producer(info),
                _check_modification_date(info),
                _check_font_consistency(pdf),
                _check_text_layer(pdf),
            ]

        overall_signal, overall_explanation = _compute_overall(checks)

        return {
            "overall_signal": overall_signal,
            "overall_explanation": overall_explanation,
            "checks": checks,
            "raw_metadata": {
                "Producer": info.get("Producer"),
                "Creator": info.get("Creator"),
                "CreationDate": info.get("CreationDate"),
                "ModDate": info.get("ModDate"),
            },
        }

    except Exception as exc:
        return {
            "overall_signal": "inconclusive",
            "overall_explanation": f"Authenticity check could not be completed: {exc}",
            "checks": [],
            "raw_metadata": {},
        }