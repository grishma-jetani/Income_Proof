import re
from datetime import datetime, date

import pdfplumber


def _clean_amount(s) -> float:
    if s is None:
        return 0.0
    cleaned = re.sub(r"[₹Rs,\s]", "", str(s)).strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_date(s: str, formats: list[str]) -> date | None:
    s = str(s or "").split("\n")[0].strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def detect_pdf_format(filepath: str) -> str:
    with pdfplumber.open(filepath) as pdf:
        text = (pdf.pages[0].extract_text() or "").lower()
    if "bank of india" in text or "bkid" in text:
        return "boi_pdf"
    if "phonepe" in text or "transaction statement for" in text:
        return "phonepe_pdf"
    return "unknown_pdf"


# ── BOI PDF parser ─────────────────────────────────────────────────────────

def parse_boi_pdf(filepath: str) -> list[dict]:
    BOI_DATE_FORMATS = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
    results = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 7:
                        continue
                    sl = str(row[0] or "").strip()
                    if not sl.isdigit():
                        continue
                    txn_date = _parse_date(row[1], BOI_DATE_FORMATS)
                    if txn_date is None:
                        continue
                    description = str(row[2] or "").strip()
                    debit = _clean_amount(row[4])
                    credit = _clean_amount(row[5])
                    balance = _clean_amount(row[6])
                    results.append({
                        "txn_date": txn_date,
                        "description": description,
                        "debit": debit,
                        "credit": credit,
                        "balance": balance if balance != 0.0 else None,
                        "source_format": "boi_pdf",
                    })
    return results

def parse_phonepe_pdf(filepath: str) -> list[dict]:
    """
    Unpacks PhonePe PDFs, natively handling "mushed" table cells where 
    multiple transactions are squashed into a single row due to missing borders.
    """
    PE_DATE_FORMATS = [
        "%b %d, %Y", "%d %b, %Y", "%B %d, %Y", 
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"
    ]
    results = []
    
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            # If standard table extraction gives nothing, try text strategy
            if not tables:
                try:
                    tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                    })
                except Exception:
                    pass
            
            for table in (tables or []):
                for row in table:
                    if not row or len(row) < 4:
                        continue
                        
                    # Extract column by column, splitting by newlines to unpack "mushed" cells
                    
                    # Col 2: Types (CREDIT / DEBIT)
                    types_raw = str(row[2]).split("\n")
                    types = [t.strip().upper() for t in types_raw if t.strip().upper() in ("CREDIT", "DEBIT")]
                    
                    # Col 3: Amounts
                    amounts_raw = str(row[3]).split("\n")
                    amounts = []
                    for a in amounts_raw:
                        clean_a = re.sub(r'[^\d.]', '', a)
                        if clean_a: amounts.append(float(clean_a))
                        
                    # Col 1: Descriptions
                    desc_text = str(row[1]).replace("\n", " ")
                    entities = re.findall(r'(?:Received from|Paid to)\s+([A-Za-z0-9]+)', desc_text, re.IGNORECASE)
                    
                    # Col 0: Dates
                    date_text = str(row[0]).replace("\n", " ")
                    dates_str = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}', date_text, re.IGNORECASE)
                    
                    # Pair them up perfectly!
                    num_txns = min(len(types), len(amounts))
                    for i in range(num_txns):
                        txn_type = types[i]
                        amount = amounts[i]
                        
                        # Safely assign the date
                        date_val = None
                        if i < len(dates_str):
                            date_val = _parse_date(dates_str[i], PE_DATE_FORMATS)
                        if not date_val and results:
                            date_val = results[-1]["txn_date"] # Fallback to previous date
                            
                        # Safely assign the description entity
                        entity = entities[i] if i < len(entities) else "Transaction"
                        prefix = "Received from" if txn_type == "CREDIT" else "Paid to"
                        
                        results.append({
                            "txn_date": date_val,
                            "description": f"{prefix} {entity}",
                            "debit": amount if txn_type == "DEBIT" else 0.0,
                            "credit": amount if txn_type == "CREDIT" else 0.0,
                            "balance": None,
                            "source_format": "phonepe_pdf",
                        })

    # Deduplicate identical rows
    unique_results = []
    seen = set()
    for r in results:
        fingerprint = f"{r['txn_date']}_{r['debit']}_{r['credit']}_{r['description']}"
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique_results.append(r)

    return unique_results
# ── Public entry point ─────────────────────────────────────────────────────

def parse_pdf(filepath: str) -> tuple[list[dict], str]:
    fmt = detect_pdf_format(filepath)
    if fmt == "boi_pdf":
        return parse_boi_pdf(filepath), fmt
    if fmt == "phonepe_pdf":
        return parse_phonepe_pdf(filepath), fmt
    return parse_boi_pdf(filepath), "unknown_pdf"